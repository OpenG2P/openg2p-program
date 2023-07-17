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
        "click button.o_Composer_buttonCancel": "triggerAddAssessment",
        "click button.o_Composer_buttonSubmit": "submitAssessment",
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
        console.log(this);
        this.assessmentAddMode = 0;
        this.assessmentAddModeStarted = 0;
    },
    _render: async function () {
        return this.$el.html(qweb.render("g2p_assessments_list", await this._getRenderingContext()));
    },
    triggerAddAssessment: function () {
        if (this.assessmentAddModeStarted === 0) {
            this.assessmentAddMode = 1;
            this.assessmentAddModeStarted = 1;
            this.$(".o_ChatterTopbar_buttonAddAssess").addClass("o_invisible_modifier");
            this.$(".o_Composer").replaceWith(
                qweb.render("g2p_assessments_add", {author_partner_id: session.partner_id})
            );
            return;
        }
        if (this.assessmentAddMode === 0) {
            this.assessmentAddMode = 1;
            this.$(".o_Composer_Assessment").removeClass("o_invisible_modifier");
            this.$(".o_ChatterTopbar_buttonAddAssess").addClass("o_invisible_modifier");
        } else {
            this.assessmentAddMode = 0;
            this.$(".o_Composer_Assessment").addClass("o_invisible_modifier");
            this.$(".o_ChatterTopbar_buttonAddAssess").removeClass("o_invisible_modifier");
        }
    },
    submitAssessment: function () {
        var self = this;
        let textareaBody = this.$("textarea.o_ComposerTextInput_textarea")[0].value;
        textareaBody = textareaBody.replace(/(?:\r\n|\r|\n)/g, "<br />");
        this._rpc({
            model: "g2p.program.assessment",
            method: "post_assessment",
            args: [textareaBody, this.resModel, this.resId],
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
        return res;
    },
});

fieldsRegistry.add("g2p_assess_widget", G2PAssessmentWizardWidget);

export {G2PAssessmentWizardWidget};
