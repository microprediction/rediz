function asyncGeneratorStep(gen, resolve, reject, _next, _throw, key, arg) { try { var info = gen[key](arg); var value = info.value; } catch (error) { reject(error); return; } if (info.done) { resolve(value); } else { Promise.resolve(value).then(_next, _throw); } }

function _asyncToGenerator(fn) { return function () { var self = this, args = arguments; return new Promise(function (resolve, reject) { var gen = fn.apply(self, args); function _next(value) { asyncGeneratorStep(gen, resolve, reject, _next, _throw, "next", value); } function _throw(err) { asyncGeneratorStep(gen, resolve, reject, _next, _throw, "throw", err); } _next(undefined); }); }; }

function LoadStreams(_x) {
  return _LoadStreams.apply(this, arguments);
}

function _LoadStreams() {
  _LoadStreams = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee(delays) {
    var url, request, dict, full_div, reg_streams, key, parsed, idx, _i, _reg_streams;

    return regeneratorRuntime.wrap(function _callee$(_context) {
      while (1) {
        switch (_context.prev = _context.next) {
          case 0:
            url = "https://api.microprediction.org/budgets/";
            // request = new Request(url, {
            //   method: 'GET'
            // });
            _context.next = 4;
            return Fetch(url);

          case 4:
            dict = _context.sent;
            full_div = document.getElementById("chooser");
            reg_streams = [];
            _context.t0 = regeneratorRuntime.keys(dict);

          case 8:
            if ((_context.t1 = _context.t0()).done) {
              _context.next = 20;
              break;
            }

            key = _context.t1.value;
            key = key.slice(0, -5); // remove ".json"

            parsed = key.split('~');
            idx = key.lastIndexOf("~");

            if (!(idx === -1)) {
              _context.next = 16;
              break;
            }

            reg_streams.push(key);
            return _context.abrupt("continue", 8);

          case 16:
            if (delays.map(String).includes(key.substr(idx + 1))) {
              _context.next = 18;
              break;
            }

            return _context.abrupt("continue", 8);

          case 18:
            _context.next = 8;
            break;

          case 20:
            for (_i = 0, _reg_streams = reg_streams; _i < _reg_streams.length; _i++) {
              stream = _reg_streams[_i];
              full_div.appendChild(SelectOption(stream));
            }

            return _context.abrupt("return", dict);

          case 22:
          case "end":
            return _context.stop();
        }
      }
    }, _callee);
  }));
  return _LoadStreams.apply(this, arguments);
}