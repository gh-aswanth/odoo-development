odoo.define('order_place_notification.WebClient', function (require) {
"use strict";

var WebClient = require('web.WebClient');
var base_bus = require('bus.Longpolling');
var session = require('web.session');

require('bus.BusService');

WebClient.include({
    show_application: function() {
        var res = this._super();
        this.start_polling();
        return res
    },
    start_polling: function() {
        this.channel_info = 'notify_info_' + session.uid;
        this.call('bus_service', 'addChannel', this.channel_info);
        this.call('bus_service', 'on', 'notification', this, this.bus_notification);
        this.call('bus_service', 'startPolling');
    },
    bus_notification: function(notifications) {
        var self = this;
        _.each(notifications, function (notification) { 
            var channel = notification[0];
            var message = notification[1];
            if (channel === self.channel_info) {
                self.on_message_info(message);
                // self.call('bus_service', 'sendNotification', message.title, message.content);
            } 
        });
    },
    on_message_info: function(message){
        var audio = new Audio('/order_place_notification/static/beep.mp3');
        audio.play();
        this.do_notify(
            message.title, 
            message.message, 
            message.sticky
            );
    }
});

});
