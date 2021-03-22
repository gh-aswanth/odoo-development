odoo.define('Jobs.EditableListRenderer', function (require) {
"use strict";

var ListRenderer = require('web.ListRenderer');

ListRenderer.include({
  _renderHeaderCell: function (node) {
        const $th = this._super.apply(this, arguments);
        if (node.attrs.class === 'job_tree_button'){
            $th.text(node.attrs.string);
        }
        return $th;
    },
});
});