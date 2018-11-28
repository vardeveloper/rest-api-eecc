var handler = {};

handler.static_url = function(src, base) {
  return [(base || 'static'), (src || '')].join('/');
};

exports.handler = handler;