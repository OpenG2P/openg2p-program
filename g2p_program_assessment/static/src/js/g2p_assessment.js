/** @odoo-module **/

import {Component, markup, onWillStart, useExternalListener, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {renderToElement} from "@web/core/utils/render";
import {session} from "@web/session";
import {useService} from "@web/core/utils/hooks";

export class G2PAssessmentWizardWidget extends Component {
    setup() {
        super.setup();
        this.orm = useService("orm");
        useExternalListener(document, "keydown", this.handleKeyUpAndInput.bind(this));
        useExternalListener(document, "click", this.handleButtonClick.bind(this));
        this.resModel = this.props.resModel
            ? this.props.resModel
            : this.props.record.evalContext.context.active_model;
        this.resId = this.props.record.resId
            ? this.props.record.resId
            : this.props.record.evalContext.context.active_id;
        this.readonly = this.props.record.readonly;
        this.rpc = useService("rpc");

        this.assessmentAddMode = 0;
        this.assessmentAddModeStarted = 0;
        this.state = useState({
            assessment: [],
            res_model: false,
            res_id_field: false,
        });

        onWillStart(async () => {
            await this._getRenderingContext();
            console.log("Options:", this.props.record, this.props.record.resModel, this.props.record.resId);
        });
    }

    handleButtonClick(ev) {
        const targetButton = $(ev.target).closest(".o_Composer_buttonSubmit");
        if (targetButton.length) {
            this.submitAssessment();
        }

        const cancelButton = $(ev.target).closest(".o_Composer_buttonCancel");
        if (cancelButton.length) {
            this.triggerAddAssessment();
        }
    }

    handleKeyUpAndInput() {
        const textarea = $("textarea.o_ComposerTextInput_textarea");

        textarea.on("keyup", () => {
            this.triggerButtonSubmitEnable();
        });

        textarea.on("input", () => {
            this.triggerButtonSubmitEnable();
        });
    }

    submitAssessment() {
        let textareaBody = $("textarea.o_ComposerTextInput_textarea")[0].value;
        textareaBody = textareaBody.replace(/(?:\r\n|\r|\n)/g, "<br />");
        const record = this.orm.call(
            "g2p.program.assessment",
            "post_assessment",
            [textareaBody, this.resModel, this.resId],
            {}
        );
        record.then(async () => {
            await this._getRenderingContext();
            this.assessmentAddMode = 0;
            this.assessmentAddModeStarted = 1;
            $(".o_Composer_Assessment").addClass("o_invisible_modifier");
            $(".o_ChatterTopbar_buttonAddAssess").removeClass("o_invisible_modifier");
        });
    }

    async _getRenderingContext() {
        try {
            const res = await this.rpc("/web/dataset/call_kw/g2p.program.assessment/get_rendering_context", {
                model: "g2p.program.assessment",
                method: "get_rendering_context",
                args: [this.resModel, this.resId],
                kwargs: {},
            });
            res.assessments.forEach((element) => {
                element.body = markup(element.body);
            });
            this.state.assessments = res.assessments;
        } catch (error) {
            console.error("Error fetching assessments:", error);
        }
    }

    triggerAddAssessment() {
        if (this.assessmentAddModeStarted === 0) {
            this.assessmentAddMode = 1;
            this.assessmentAddModeStarted = 1;
            $(".o_ChatterTopbar_buttonAddAssess").addClass("o_invisible_modifier");
            $(".o_Composer").replaceWith(
                renderToElement("g2p_assessments_add", {author_partner_id: session.partner_id})
            );
            return;
        }
        if (this.assessmentAddMode === 0) {
            this.assessmentAddMode = 1;
            $(".o_Composer_Assessment").removeClass("o_invisible_modifier");
            $(".o_ChatterTopbar_buttonAddAssess").addClass("o_invisible_modifier");
        } else {
            this.assessmentAddMode = 0;
            $(".o_Composer_Assessment").addClass("o_invisible_modifier");
            $(".o_ChatterTopbar_buttonAddAssess").removeClass("o_invisible_modifier");
        }
    }

    triggerButtonSubmitEnable() {
        const textareaValue = $("textarea.o_ComposerTextInput_textarea").val();
        const isButtonDisabled = textareaValue.trim() === "";
        $("button.o_Composer_buttonSubmit").prop("disabled", isButtonDisabled);
    }
}

G2PAssessmentWizardWidget.template = "g2p_assessments_list";

export const assessmentwizard = {
    component: G2PAssessmentWizardWidget,
    extractProps(fieldInfo) {
        const {options} = fieldInfo;
        const {res_model: resModel, res_id_field: resIdField} = options;
        return {
            resModel,
            resIdField,
        };
    },
};

registry.category("fields").add("g2p_assess_widget", assessmentwizard);
