/** @odoo-module **/

import AbstractField from "web.AbstractField";
import fieldsRegistry from "web.field_registry";
import {qweb} from "web.core";
import session from "web.session";

// eslint-disable-next-line no-undef
const markup = QWeb2.tools.markup;

// The following to be replaced with Widget instead of FieldText
var G2PAssessmentWizardWidget = AbstractField.extend({
    className: "o_field_g2p_program_assessment",
    tagName: "div",
    events: {
        "click button.o_ChatterTopbar_buttonAddAssess": "triggerAddAssessment",
        "click button.o_ChatterTopbar_buttonAddComment": "triggerAddComment",
        "click button.o_Composer_buttonCancel": "triggerAddAssessment",
        "click button.o_Composer_buttonSubmit": "submitAssessment",
        // "click button.o_Composer_buttonSubmit": "submitComment",
        "keyup textarea.o_ComposerTextInput_textarea": "triggerButtonSubmitEnable",
    },
    init: function () {
        this._super.apply(this, arguments);
        this.resModel = this.nodeOptions.res_model ? this.nodeOptions.res_model : this.value.model;
        this.resId = this.nodeOptions.res_id_field
            ? this.recordData[this.nodeOptions.res_id_field]
            : this.value.data.id;
        this.readonly = false;
        if (this.nodeOptions.readonly) {
            this.readonly = this.nodeOptions.readonly;
        } else if (this.nodeOptions.readonly_field) {
            this.readonly = this.recordData[this.nodeOptions.readonly_field];
        } else if (this.nodeOptions.not_readonly_field) {
            this.readonly = !this.recordData[this.nodeOptions.not_readonly_field];
        }
        this.showAddCommentsButton = this.nodeOptions.show_add_comments_button !== false;
        this.showAddAssessmentsButton = this.nodeOptions.show_add_assessments_button !== false;
        console.log(this);
        this.assessmentAddMode = 0;
        this.assessmentAddModeStarted = 0;
    },
    _render: async function () {
        return this.$el.html(qweb.render("g2p_assessments_list", await this._getRenderingContext()));
    },
    triggerAddComment: function (e) {
        return this.triggerAddAssessment(e, true);
    },
    triggerAddAssessment: function (e, is_comment = false) {
        if (this.assessmentAddModeStarted === 0) {
            this.assessmentAddMode = 1;
            this.assessmentAddModeStarted = 1;
            this.$(".o_Composer_header_buttons").addClass("o_invisible_modifier");
            this.$(".o_Composer").replaceWith(
                qweb.render("g2p_assessments_add", {author_partner_id: session.partner_id})
            );
        } else if (this.assessmentAddMode === 0) {
            this.assessmentAddMode = 1;
            this.$(".o_Composer_Assessment").removeClass("o_invisible_modifier");
            this.$(".o_Composer_header_buttons").addClass("o_invisible_modifier");
        } else {
            this.assessmentAddMode = 0;
            this.$(".o_Composer_Assessment").addClass("o_invisible_modifier");
            this.$(".o_Composer_header_buttons").removeClass("o_invisible_modifier");
        }
        console.log("trigger ", is_comment);
        if (is_comment) this.$(".o_Composer_Assessment").addClass("o_Composer_Comment");
        else this.$(".o_Composer_Assessment").removeClass("o_Composer_Comment");
    },
    submitAssessment: function () {
        var self = this;
        const is_comment = this.$(".o_Composer_Assessment").hasClass("o_Composer_Comment");
        console.log(is_comment);
        let textareaBody = this.$("textarea.o_ComposerTextInput_textarea")[0].value;
        textareaBody = textareaBody.replace(/(?:\r\n|\r|\n)/g, "<br />");
        this._rpc({
            model: "g2p.program.assessment",
            method: "post_assessment",
            args: [textareaBody, this.resModel, this.resId, is_comment],
        }).then(function () {
            self.assessmentAddMode = 0;
            self.assessmentAddModeStarted = 0;
            self._render();
        });
    },
    triggerButtonSubmitEnable: function () {
        this.$("button.o_Composer_buttonSubmit").prop(
            "disabled",
            this.$("textarea.o_ComposerTextInput_textarea")[0].value === ""
        );
    },
    _getRenderingContext: async function () {
        const res = await this._rpc({
            model: "g2p.program.assessment",
            method: "get_rendering_context",
            args: [this.resModel, this.resId],
        });
        // To ask odoo to consider the body as html
        res.assessments.forEach((element) => {
            element.body = markup(element.body);
        });
        res.readonly = this.readonly;
        res.resModel = this.resModel;
        res.showAddCommentsButton = this.showAddCommentsButton;
        res.showAddAssessmentsButton = this.showAddAssessmentsButton;
        return res;
    },
});

fieldsRegistry.add("g2p_assess_widget", G2PAssessmentWizardWidget);

export {G2PAssessmentWizardWidget};
