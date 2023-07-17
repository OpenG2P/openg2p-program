odoo.define("g2p_program_documents.legacy.DocumentViewer", function (require) {
    var core = require("web.core");
    var Widget = require("web.Widget");
    var QWeb = core.qweb;

    var SCROLL_ZOOM_STEP = 0.1;
    var ZOOM_STEP = 0.5;

    var DocumentViewer = Widget.extend({
        template: "g2p_DocumentViewer",
        events: {
            "click .o_download_btn": "_onDownload",
            "click .o_viewer_img": "_onImageClicked",
            "click .o_viewer_video": "_onVideoClicked",
            "click .o_rotate": "_onRotate",
            "click .o_zoom_in": "_onZoomIn",
            "click .o_zoom_out": "_onZoomOut",
            "click .o_zoom_reset": "_onZoomReset",
            "click .o_close_btn, .o_viewer_img_wrapper": "_onClose",
            "DOMMouseScroll .o_viewer_content": "_onScroll", // Firefox
            "mousewheel .o_viewer_content": "_onScroll", // Chrome, Safari, IE
            "mousedown .o_viewer_img": "_onStartDrag",
            "mousemove .o_viewer_content": "_onDrag",
            "mouseup .o_viewer_content": "_onEndDrag",
        },

        init: function (parent, attachments, activeAttachmentID) {
            this._super(parent);
            this.attachment = _.filter(attachments, function (attachment) {
                var match =
                    attachment.type === "url"
                        ? attachment.url.match("(youtu|.png|.jpg|.gif)")
                        : attachment.mimetype.match("(image|video|application/pdf|text)");
                if (match) {
                    attachment.fileType = match[1];
                    if (match[1].match("(.png|.jpg|.gif)")) {
                        attachment.fileType = "image";
                    }
                    if (match[1] === "youtu") {
                        var youtube_array = attachment.url.split("/");
                        var youtube_token = youtube_array[youtube_array.length - 1];
                        if (youtube_token.indexOf("watch") !== -1) {
                            youtube_token = youtube_token.split("v=")[1];
                            var amp = youtube_token.indexOf("&");
                            if (amp !== -1) {
                                youtube_token = youtube_token.substring(0, amp);
                            }
                        }
                        attachment.youtube = youtube_token;
                    }
                    return true;
                }
            });
            this.activeAttachment = _.findWhere(attachments, {id: activeAttachmentID});
            this.modelName = "ir.attachment";
            this._reset();
        },

        start: function () {
            this.$el.modal("show");
            this.$el.on("hidden.bs.modal", this._onDestroy.bind(this));
            this.$(".o_viewer_img").on("load", this._onImageLoaded.bind(this));
            this.$('[data-toggle="tooltip"]').tooltip({delay: 0});
            return this._super.apply(this, arguments);
        },

        destroy: function () {
            if (this.isDestroyed()) {
                return;
            }
            this.trigger_up("document_viewer_closed");
            this.$el.modal("hide");
            this.$el.remove();
            this._super.apply(this, arguments);
        },

        _reset: function () {
            this.scale = 1;
            this.dragStartX = this.dragstopX = 0;
            this.dragStartY = this.dragstopY = 0;
        },

        _updateContent: function () {
            this.$(".o_viewer_content").html(
                QWeb.render("g2p.DocumentViewer.Content", {
                    widget: this,
                })
            );

            this.$(".o_viewer_img").on("load", this._onImageLoaded.bind(this));
            this.$('[data-toggle="tooltip"]').tooltip({delay: 0});
            this._reset();
        },

        _getTransform: function (scale, angle) {
            return "scale3d(" + scale + ", " + scale + ", 1) rotate(" + angle + "deg)";
        },

        _rotate: function (angle) {
            this._reset();
            var new_angle = (this.angle || 0) + angle;
            this.$(".o_viewer_img").css("transform", this._getTransform(this.scale, new_angle));
            this.$(".o_viewer_img").css("max-width", new_angle % 180 !== 0 ? $(document).height() : "100%");
            this.$(".o_viewer_img").css("max-height", new_angle % 180 !== 0 ? $(document).width() : "100%");
            this.angle = new_angle;
        },

        _zoom: function (scale) {
            if (scale > 0.5) {
                this.$(".o_viewer_img").css("transform", this._getTransform(scale, this.angle || 0));
                this.scale = scale;
            }
            this.$(".o_zoom_reset")
                .add(".o_zoom_out")
                .toggleClass("disabled", scale === 1);
        },

        _onClose: function (e) {
            e.preventDefault();
            this.destroy();
        },

        _onDestroy: function () {
            this.destroy();
        },

        _onDownload: function (e) {
            e.preventDefault();
            window.location.href =
                "/web/content/" +
                this.modelName +
                "/" +
                this.activeAttachment.id +
                "/" +
                "datas" +
                "?download=true";
        },

        _onDrag: function (e) {
            e.preventDefault();
            if (this.enableDrag) {
                var $image = this.$(".o_viewer_img");
                var $zoomer = this.$(".o_viewer_zoomer");
                var top =
                    $image.prop("offsetHeight") * this.scale > $zoomer.height()
                        ? e.clientY - this.dragStartY
                        : 0;
                var left =
                    $image.prop("offsetWidth") * this.scale > $zoomer.width()
                        ? e.clientX - this.dragStartX
                        : 0;
                $zoomer.css("transform", "translate3d(" + left + "px, " + top + "px, 0)");
                $image.css("cursor", "move");
            }
        },

        _onEndDrag: function (e) {
            e.preventDefault();
            if (this.enableDrag) {
                this.enableDrag = false;
                this.dragstopX = e.clientX - this.dragStartX;
                this.dragstopY = e.clientY - this.dragStartY;
                this.$(".o_viewer_img").css("cursor", "");
            }
        },

        _onImageClicked: function (e) {
            e.stopPropagation();
        },

        _onImageLoaded: function () {
            this.$(".o_loading_img").hide();
        },

        _onKeyUp: function (e) {
            switch (e.which) {
                case $.ui.keyCode.ESCAPE:
                    e.preventDefault();
                    this._onClose(e);
                    break;
            }
        },

        _onScroll: function (e) {
            var scale;
            if (e.originalEvent.wheelDelta > 0 || e.originalEvent.detail < 0) {
                scale = this.scale + SCROLL_ZOOM_STEP;
                this._zoom(scale);
            } else {
                scale = this.scale - SCROLL_ZOOM_STEP;
                this._zoom(scale);
            }
        },

        _onStartDrag: function (e) {
            e.preventDefault();
            this.enableDrag = true;
            this.dragStartX = e.clientX - (this.dragstopX || 0);
            this.dragStartY = e.clientY - (this.dragstopY || 0);
        },

        _onVideoClicked: function (e) {
            e.stopPropagation();
            var videoElement = e.target;
            if (videoElement.paused) {
                videoElement.play();
            } else {
                videoElement.pause();
            }
        },

        _onRotate: function (e) {
            e.preventDefault();
            this._rotate(90);
        },

        _onZoomIn: function (e) {
            e.preventDefault();
            var scale = this.scale + ZOOM_STEP;
            this._zoom(scale);
        },

        _onZoomOut: function (e) {
            e.preventDefault();
            var scale = this.scale - ZOOM_STEP;
            this._zoom(scale);
        },

        _onZoomReset: function (e) {
            e.preventDefault();
            this.$(".o_viewer_zoomer").css("transform", "");
            this._zoom(1);
        },
    });

    return DocumentViewer;
});

odoo.define("g2p_program_documents.form_controller_one2many", function (require) {
    var FormController = require("web.FormController");
    var DocumentViewer = require("g2p_program_documents.legacy.DocumentViewer");

    FormController.include({
        updateButtons: function () {
            this._super.apply(this, arguments);
            var self = this;
            this.renderer.$(".o_data_row .o_list_button_preview").click(function (ev) {
                var slugField = "slug";
                var $slugElement = $(ev.currentTarget)
                    .closest(".o_data_row")
                    .find('.o_list_char[name="' + slugField + '"]');
                var slugText = $slugElement.text();
                var recordID;
                if (slugText.includes("-")) {
                    var parts = slugText.split("-");
                    var lastPart = parts[parts.length - 1].split(".")[0];
                    if (!isNaN(lastPart)) {
                        recordID = parseInt(lastPart);
                    }
                }
                if (recordID) {
                    self._onPreviewButtonClick(recordID);
                }
            });
        },

        _onPreviewButtonClick: function (recordID) {
            var self = this;
            this._rpc({
                model: "storage.file",
                method: "get_binary",
                args: [[recordID]],
            }).then(function (result) {
                var attach_id = parseInt(result.id);
                var mimetype = result.mimetype;
                var indexContent = result.index_content || "";
                if (mimetype.includes("image")) {
                    var attachments = [
                        {
                            id: attach_id,
                            mimetype: mimetype,
                            fileType: indexContent,
                        },
                    ];
                    var attachmentViewer = new DocumentViewer(self, attachments, attach_id);
                    attachmentViewer.appendTo($("body"));
                } else {
                    window.open(result.url, "_blank");
                }
            });
        },
    });
});
