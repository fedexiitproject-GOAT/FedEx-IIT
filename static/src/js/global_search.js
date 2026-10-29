/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class FedexGlobalSearch extends Component {
    static template = "fedex_repository.GlobalSearch";
    static props = { "*": true };
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({q: "", results: []});
        this.open = this.open.bind(this);
        this.search = this.search.bind(this);
    }
    async search() { this.state.results = await this.orm.call("fedex.project", "global_search", [this.state.q]); }
    open(result) { this.action.doAction({type: "ir.actions.act_window", res_model: result.model, res_id: result.id, view_mode: "form"}); }
}
registry.category("actions").add("fedex_repository_global_search", FedexGlobalSearch);
