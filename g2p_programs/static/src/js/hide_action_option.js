odoo.define("g2p_programs.BasicView", function (require) {
    var BasicView = require("web.BasicView");
    BasicView.include({
        init: function (viewInfo) {
            var self = this;
            this._super.apply(this, arguments);
            const model = ["g2p.program_membership"];

            if (model.includes(self.controllerParams.modelName)) {
                self.controllerParams.archiveEnabled = "False" in viewInfo.fields;
            }
        },
    });
});
