odoo.define("g2p_program_assessment.entitlement_validation", function (require) {
    var core = require("web.core");
    var _t = core._t;
    var Dialog = require("web.Dialog");
    var FormController = require("web.FormController");

    FormController.include({
        _onButtonClicked: function (event) {
            var self = this;
            var buttonName = event.data.attrs.name;
            if (buttonName === "create_entitlement") {
                var initialAmount = parseFloat(this.$el.find(".o_field_monetary input").val());
                if (!initialAmount || initialAmount <= 0) {
                    Dialog.alert(self, _t("Amount cannot be zero or empty or negative"));
                } else {
                    // For other buttons, execute the original behavior
                    this._super.apply(this, arguments);
                }
            } else {
                // For other buttons, execute the original behavior
                this._super.apply(this, arguments);
            }
        },
    });
});
