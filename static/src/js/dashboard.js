/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { WebClient } from "@web/webclient/webclient";

patch(WebClient.prototype, {
    setup() {
        super.setup();
        const updateFedexThemeScope = () => {
            const currentApp = this.menuService?.getCurrentApp?.();
            const currentAction = this.actionService?.currentController?.action;
            const isFedexMenu = currentApp?.xmlid === "fedex_repository.menu_fedex_root";
            const isFedexAction = Boolean(
                currentAction &&
                (String(currentAction.res_model || "").startsWith("fedex.") ||
                 String(currentAction.tag || "").startsWith("fedex_repository") ||
                 String(currentAction.xml_id || "").startsWith("fedex_repository."))
            );
            const isFedex = Boolean(isFedexMenu || (!currentApp && isFedexAction));
            document.body?.classList.toggle("o_fedex_app", isFedex);
            document.querySelector(".o_web_client")?.classList.toggle("o_fedex_app", isFedex);
        };
        this.env.bus.addEventListener("MENUS:APP-CHANGED", updateFedexThemeScope);
        this.env.bus.addEventListener("ACTION_MANAGER:UI-UPDATED", updateFedexThemeScope);
        this.env.bus.addEventListener("ACTION_MANAGER:UPDATE", updateFedexThemeScope);
        this.env.bus.addEventListener("WEB_CLIENT_READY", updateFedexThemeScope);
    },
});

const STATUS_LABELS = {
    yet_to_start: "Yet To Start",
    new_project: "New Project",
    in_progress: "In Progress",
    completed: "Completed",
    on_hold: "On Hold",
    cancelled: "Cancelled",
};
const VERTICAL_LABELS = {
    supply_chain: "Supply Chain Sustainability and Modelling",
    worker_wellness: "Logistics Worker Wellness",
    algorithms_ml: "Algorithms and Machine Learning",
    infrastructure: "Logistics Infrastructure",
    unassigned: "Not assigned",
};

class FedexDashboard extends Component {
    static template = "fedex_repository.Dashboard";
    static props = { "*": true };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: {}, loading: true, error: false });
        this.open = this.open.bind(this);
        onWillStart(async () => {
            try {
                this.state.data = await this.orm.call("fedex.project", "dashboard_data", []);
            } catch (error) {
                this.state.error = true;
            } finally {
                this.state.loading = false;
            }
        });
    }

    open(xmlid) {
        return this.action.doAction(xmlid);
    }

    chartRows(rows, key) {
        return (rows || []).map((row) => {
            let label = row[key] || "Unassigned";
            if (Array.isArray(label)) label = label[1] || "Unassigned";
            if (key === "state") label = STATUS_LABELS[label] || label;
            if (key === "vertical") label = VERTICAL_LABELS[label] || label;
            return { label, count: Number(row.id_count || row.__count || 0) };
        });
    }
}
registry.category("actions").add("fedex_repository_dashboard", FedexDashboard);
