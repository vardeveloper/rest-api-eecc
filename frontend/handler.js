var handler = {};

if (process.argv && process.argv.indexOf('--deploy') != -1) {
  handler.deploy = true;
}

handler.static_url = function(src, base) {
  return [(base || 'static'), (src || '')].join('/');
};

exports.handler = handler;