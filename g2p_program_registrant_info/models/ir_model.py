from odoo.tools.safe_eval import wrap_module

from odoo.addons.base.models import ir_model

ir_model.SAFE_EVAL_BASE.update({"json": wrap_module(__import__("json"), ["loads", "dumps"])})
