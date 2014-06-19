// https://github.com/grafana/grafana/blob/master/src/config.sample.js
define(['settings'],
function (Settings) {
  return new Settings({
    elasticsearch: "http://"+window.location.hostname+":9200",
    graphiteUrl: "http://"+window.location.hostname+":8080",
    default_route: '/dashboard/file/default.json',
    timezoneOffset: null,
    grafana_index: "grafana-dash",
    panel_names: [
      'text',
      'graphite'
    ]
  });
});
