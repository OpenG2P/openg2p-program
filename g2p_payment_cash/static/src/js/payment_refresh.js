odoo.define("g2p_payment_cash.payment_refresh", function (require) {
    var FormController = require("web.FormController");
    FormController.include({
        _onOpenOne2ManyRecord: function (ev) {
            var self = this;
            var originalFunction = this._super.bind(this);
            var data = ev.data.field.relation;
            $(document).on("click", function (event) {
                var childtarget = event.target.innerText;
                var className = event.target.className;
                if (data === "g2p.entitlement") {
                    if (
                        className === "o_form_button_cancel" ||
                        className === "close" ||
                        childtarget === "Close"
                    ) {
                        // #refresh the screen
                        self.reload();
                    }
                }
            });
            originalFunction(ev);
        },
    });
});
