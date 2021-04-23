function _createForOfIteratorHelper(o, allowArrayLike) { var it; if (typeof Symbol === "undefined" || o[Symbol.iterator] == null) { if (Array.isArray(o) || (it = _unsupportedIterableToArray(o)) || allowArrayLike && o && typeof o.length === "number") { if (it) o = it; var i = 0; var F = function F() {}; return { s: F, n: function n() { if (i >= o.length) return { done: true }; return { done: false, value: o[i++] }; }, e: function e(_e) { throw _e; }, f: F }; } throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); } var normalCompletion = true, didErr = false, err; return { s: function s() { it = o[Symbol.iterator](); }, n: function n() { var step = it.next(); normalCompletion = step.done; return step; }, e: function e(_e2) { didErr = true; err = _e2; }, f: function f() { try { if (!normalCompletion && it.return != null) it.return(); } finally { if (didErr) throw err; } } }; }

function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }

function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) { arr2[i] = arr[i]; } return arr2; }

function asyncGeneratorStep(gen, resolve, reject, _next, _throw, key, arg) { try { var info = gen[key](arg); var value = info.value; } catch (error) { reject(error); return; } if (info.done) { resolve(value); } else { Promise.resolve(value).then(_next, _throw); } }

function _asyncToGenerator(fn) { return function () { var self = this, args = arguments; return new Promise(function (resolve, reject) { var gen = fn.apply(self, args); function _next(value) { asyncGeneratorStep(gen, resolve, reject, _next, _throw, "next", value); } function _throw(err) { asyncGeneratorStep(gen, resolve, reject, _next, _throw, "throw", err); } _next(undefined); }); }; }
var json_name = 'hospital_bike_activity.json';
var base_url = 'https://api.microprediction.org/';
var stream, horizon, json_name, delays, primary, dict;
var globalList;
var url = base_url + "leaderboards/" + json_name;
// var request = new Request(url, {
//   method: 'GET'
// });
var space_div = document.createElement("div");
var testDelays = [70, 310, 910, 3555];
space_div.id = "space";
$(window).load(function () {
  LoadConStreams();
  LoadPrizes();
  var dict = LoadStreams([70, 310, 910, 3555]).then(function (res) {
    var streamName = $('.chooser #chooser').val();
    LoadBardata(streamName);
  });
});
$('.chooser select').change(function () {
  $(this).addClass('changed');

  if ($('#chooser.changed').length) {
    $('#secondary-chooser').val('');
    $('#tertiary-chooser').val('');
  } //   Empty current sections to make room for new data


  $('#dashboard-leaderboard').empty();
  $('#dashboard-lagged').empty();
  var graph = $("#dashboard-bargraph"); //   Plotly.purge(graph);
  //   graph.empty();

  var streamName = $('#chooser').val();
  LoadBardata(streamName);
});

function LoadBardata(_x) {
  return _LoadBardata.apply(this, arguments);
}

function _LoadBardata() {
  _LoadBardata = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee(streamName) {
    var barBase, url, request, value, data;
    return regeneratorRuntime.wrap(function _callee$(_context) {
      while (1) {
        switch (_context.prev = _context.next) {
          case 0:
            barBase = 'https://plots.microprediction.org/';
            url = barBase + "bar?name=" + streamName + '.json&json=True';
            // request = new Request(url, {
            //   method: 'GET'
            // });
            _context.next = 5;
            return Fetch(url);

          case 5:
            value = _context.sent;
            data = JSON.parse(value);
            OnLoadStreamDashboard(data, testDelays);

          case 8:
          case "end":
            return _context.stop();
        }
      }
    }, _callee);
  }));
  return _LoadBardata.apply(this, arguments);
}

function OnLoadStreamDashboard(_x2, _x3) {
  return _OnLoadStreamDashboard.apply(this, arguments);
}

function _OnLoadStreamDashboard() {
  _OnLoadStreamDashboard = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee2(plot_x, all_delays) {
    return regeneratorRuntime.wrap(function _callee2$(_context2) {
      while (1) {
        switch (_context2.prev = _context2.next) {
          case 0:
            delays = all_delays.map(String); //     stream = GetUrlVars()["stream"];
            //     horizon = GetUrlVars()["horizon"];

            primary = document.getElementById('chooser').value;
            secondarySel = document.getElementById('secondary-chooser');
            secondary = secondarySel.value;
            tertiarySel = document.getElementById('tertiary-chooser');
            tertiary = tertiarySel.value;
            stream = primary;

            if (secondarySel.classList.contains('changed')) {
              tertiarySel.selectedIndex = 1;
            }

            if (secondary != '') {
              tertiary = tertiarySel.value;
              stream = secondary + primary + tertiary;
            } else {
              tertiarySel.selectedIndex = 0;
            }

            if ($('.chooser select.changed').length) {
              valChecker(primary, secondary, tertiary);
            }

            if (horizon && !delays.includes(horizon)) {
              horizon = delays[0];
            }

            if (!horizon) {
              json_name = stream + ".json";
            } else {
              json_name = horizon + "::" + stream + ".json";
            }

            LoadDashboardName();
            _context2.next = 15;
            return LoadLeaderboard();

          case 15:
            LoadHorizon();
            LoadButtonStream();
            LoadCurrentValue();
            LoadLagged();

            if (horizon) {
              LoadCDF(plot_x);
            } else {
              if ($('.chooser .changed').length) {
                reLoadBarGraph(plot_x);
                $('.chooser .changed').removeClass('changed');
              } else {
                LoadBarGraph(plot_x);
              }
            }

          case 20:
          case "end":
            return _context2.stop();
        }
      }
    }, _callee2);
  }));
  return _OnLoadStreamDashboard.apply(this, arguments);
}

function LoadDashboardName() {
  document.getElementById("box-stream-name").innerText = stream;
}

function LoadCurrentValue() {
  return _LoadCurrentValue.apply(this, arguments);
}

function _LoadCurrentValue() {
  _LoadCurrentValue = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee3() {
    var url, request, value;
    return regeneratorRuntime.wrap(function _callee3$(_context3) {
      while (1) {
        switch (_context3.prev = _context3.next) {
          case 0:
            url = base_url + "live/" + json_name;
            // request = new Request(url, {
            //   method: 'GET'
            // });
            _context3.next = 4;
            return Fetch(url);

          case 4:
            value = _context3.sent;

            if (value !== "null") {
              document.getElementById("box-current-value").style.display = "block";
              document.getElementById("box-current-value-value").innerText = Round(parseFloat(value), 5);
            } else {
              document.getElementById("box-current-value").style.display = "none";
            }

          case 6:
          case "end":
            return _context3.stop();
        }
      }
    }, _callee3);
  }));
  return _LoadCurrentValue.apply(this, arguments);
}

function LoadHorizon() {
  if (!horizon) {
    document.getElementById("box-horizon").style.display = "none";
    return;
  }

  document.getElementById("box-horizon").style.display = "inline";
  var button_group = document.getElementById("box-horizon-button-group");

  var _iterator = _createForOfIteratorHelper(delays),
      _step;

  try {
    var _loop = function _loop() {
      var delay = _step.value;
      var btn = document.createElement("button");
      btn.innerText = delay + " sec";

      btn.onclick = function () {
        window.location = "stream_dashboard.html?stream=" + stream + "&horizon=" + delay;
      }; // current button


      if (delay === horizon) {
        btn.style.backgroundColor = "#8f3566";
        btn.style.color = "#f9c809";
        btn.style.fontWeight = "bold";
      }

      button_group.appendChild(btn);
    };

    for (_iterator.s(); !(_step = _iterator.n()).done;) {
      _loop();
    }
  } catch (err) {
    _iterator.e(err);
  } finally {
    _iterator.f();
  }
}

function LoadButtonStream() {
  // IF THERE IS A HORIZON AKA "70::", HAVE A "GO TO STREAM" BUTTON
  if (horizon) {
    var button = document.getElementById("box-button-left");
    button.innerHTML = "Go to Stream &rarr;";
    button.style.display = "inline";

    button.onclick = function () {
      window.location = "stream_dashboard.html?stream=" + stream;
    }; // OTHERWISE, IF IT IS A Z STREAM, HAVE A "GO TO COMPETITIONS" BUTTON AND A "GO TO PARENT" NAV

  } else if (stream.includes("z1") || stream.includes("z2") || stream.includes("z3")) {
    var l_button = document.getElementById("box-button-left");
    l_button.innerHTML = "&larr; Go to Competitions";
    l_button.style.display = "inline";

    l_button.onclick = function () {
      window.location = "stream_dashboard.html?stream=" + stream + "&horizon=70";
    };

    if (stream.includes("z1")) {
      var r_button = document.getElementById("box-button-right");
      r_button.innerHTML = "Go to Parent &rarr;";
      r_button.style.display = "inline";
      var first = stream.indexOf("~") + 1;
      var last = stream.lastIndexOf("~");

      r_button.onclick = function () {
        window.location = "stream_dashboard.html?stream=" + stream.slice(first, last);
      };
    } else {
      var button_div = document.getElementsByClassName("dropdown2")[0];
      var streams = [];
      var search_idx = 3;

      while (stream.indexOf('~', search_idx) !== -1) {
        streams.push(stream.slice(search_idx, stream.indexOf('~', search_idx)));
        search_idx = stream.indexOf('~', search_idx) + 1;
      }

      var _button = document.getElementById("dropbtn2");

      var button_content = document.getElementById("dropdown");
      _button.innerHTML = "Go to Parent &rarr;";
      button_div.style.display = "inline-flex";

      for (var _i = 0, _streams = streams; _i < _streams.length; _i++) {
        var _stream = _streams[_i];
        var a = document.createElement("a");
        a.href = "stream_dashboard.html?stream=" + _stream;
        a.innerText = _stream;
        a.style.display = "block";
        button_content.appendChild(a);
      }

      _button.onclick = function () {
        document.getElementById("dropdown").classList.toggle("show");
      };
    } // ELSE, IT IS JUST A NORMAL STREAM AKA "BART_DELAYS.JSON"
    // SHOW A "GO TO COMPETITIONS" AND A "GO TO Z1" DROPDOWN

  } else {
    var _l_button = document.getElementById("box-button-left");

    _l_button.innerHTML = "&larr; Go to Competitions";
    _l_button.style.display = "inline";

    _l_button.onclick = function () {
      window.location = "stream_dashboard.html?stream=" + stream + "&horizon=70";
    };

    var _button_div = document.getElementsByClassName("dropdown2")[0];

    var _button2 = document.getElementById("dropbtn2");

    var _button_content = document.getElementById("dropdown");

    _button2.innerHTML = " &larr; Go to Z1";
    _button_div.style.display = "inline-flex";
    var new_delays = [delays[0], delays[delays.length - 1]];

    for (var _i2 = 0, _new_delays = new_delays; _i2 < _new_delays.length; _i2++) {
      var delay = _new_delays[_i2];

      var _a = document.createElement("a");

      _a.href = "stream_dashboard.html?stream=z1~" + stream.slice(first, last) + "~" + delay;
      _a.innerText = delay + " sec";
      _a.style.display = "block";

      _button_content.appendChild(_a);
    }

    _button2.onclick = function () {
      document.getElementById("dropdown").classList.toggle("show");
    };
  }
}

function LoadLeaderboard() {
  return _LoadLeaderboard.apply(this, arguments);
}

function _LoadLeaderboard() {
  _LoadLeaderboard = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee4() {
    var url, request, dict, table, new_row, _i3, _arr, header_cell, place, _new_row, new_cell;

    return regeneratorRuntime.wrap(function _callee4$(_context4) {
      while (1) {
        switch (_context4.prev = _context4.next) {
          case 0:
            url = base_url + "leaderboards/" + json_name;
            // request = new Request(url, {
            //   method: 'GET'
            // });
            _context4.next = 4;
            return Fetch(url);

          case 4:
            dict = _context4.sent;
            leaderboard_div = document.getElementById("dashboard-leaderboard");

            if (!(Object.keys(dict).length === 0)) {
              _context4.next = 10;
              break;
            }

            leaderboard_div.appendChild(TextDiv("No leaderboard available.", null, null, null, true));
            leaderboard_div.appendChild(space_div);
            return _context4.abrupt("return");

          case 10:
            table = document.createElement("TABLE");
            table.classList.add("default-table");
            table.classList.add("default-table-small");
            table.classList.add("leaderboard-table");
            new_row = table.insertRow(-1);

            for (_i3 = 0, _arr = ["Rank", "MUID", "Points"]; _i3 < _arr.length; _i3++) {
              head = _arr[_i3];
              header_cell = document.createElement("TH");
              header_cell.innerHTML = head;
              new_row.appendChild(header_cell);
            }

            place = 1;

            for (name in dict) {
              _new_row = table.insertRow(-1);
              new_cell = _new_row.insertCell(-1);
              new_cell.appendChild(TextDiv(place));
              new_cell = _new_row.insertCell(-1);
              new_cell.appendChild(TextDiv(name));
              new_cell = _new_row.insertCell(-1);
              new_cell.appendChild(TextDiv(dict[name], true, 3));
              place = place + 1;
            }

            leaderboard_div.appendChild(table);

          case 19:
          case "end":
            return _context4.stop();
        }
      }
    }, _callee4);
  }));
  return _LoadLeaderboard.apply(this, arguments);
}

function LoadPrizes() {
  return _LoadPrizes.apply(this, arguments);
}

function _LoadPrizes() {
  _LoadPrizes = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee5() {
    var url, conv_url, request, dict, table, new_row, _i4, _arr2, header_cell, _new_row2, new_cell, parts, last_part, this_item, sing_request, sing_dict;

    return regeneratorRuntime.wrap(function _callee5$(_context5) {
      while (1) {
        switch (_context5.prev = _context5.next) {
          case 0:
            url = base_url + "prizes/";
            conv_url = "https://devapi.microprediction.org/animal/";
            // request = new Request(url, {
            //   method: 'GET'
            // });
            _context5.next = 5;
            return Fetch(url);

          case 5:
            dict = _context5.sent;
            prizes_div = document.getElementById("prizes-dashboard");

            if (!(Object.keys(dict).length === 0)) {
              _context5.next = 11;
              break;
            }

            prizes_div.appendChild(TextDiv("No prizes available.", null, null, null, true));
            prizes_div.appendChild(space_div);
            return _context5.abrupt("return");

          case 11:
            table = document.createElement("TABLE");
            table.classList.add("default-table");
            table.classList.add("default-table-small");
            table.classList.add("leaderboard-table");
            new_row = table.insertRow(-1);

            for (_i4 = 0, _arr2 = ["Sponsor", "Value"]; _i4 < _arr2.length; _i4++) {
              head = _arr2[_i4];
              header_cell = document.createElement("TH");
              header_cell.innerHTML = head;
              new_row.appendChild(header_cell);
            }

            _context5.t0 = regeneratorRuntime.keys(dict);

          case 18:
            if ((_context5.t1 = _context5.t0()).done) {
              _context5.next = 34;
              break;
            }

            name = _context5.t1.value;
            _new_row2 = table.insertRow(-1);
            new_cell = _new_row2.insertCell(-1);
            parts = name.split("/");
            last_part = parts[parts.length - 1];
            this_item = conv_url + last_part;
            // sing_request = new Request(this_item, {
            //   method: 'GET'
            // });
            _context5.next = 28;
            return Fetch(this_item);

          case 28:
            sing_dict = _context5.sent;
            new_cell.appendChild(TextDiv(sing_dict));
            new_cell = _new_row2.insertCell(-1);
            new_cell.appendChild(TextDiv(dict[name], true, 3));
            _context5.next = 18;
            break;

          case 34:
            prizes_div.appendChild(table);

          case 35:
          case "end":
            return _context5.stop();
        }
      }
    }, _callee5);
  }));
  return _LoadPrizes.apply(this, arguments);
}

function LoadLagged() {
  return _LoadLagged.apply(this, arguments);
}

function _LoadLagged() {
  _LoadLagged = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee6() {
    var url, request, lagged_values, table, new_row, headers, _i5, _headers, header_cell, i, _iterator2, _step2, _new_row3, new_cell;

    return regeneratorRuntime.wrap(function _callee6$(_context6) {
      while (1) {
        switch (_context6.prev = _context6.next) {
          case 0:
            url = base_url + "lagged/" + stream + ".json";
            // request = new Request(url, {
            //   method: 'GET'
            // });
            _context6.next = 5;
            return Fetch(url);

          case 5:
            lagged_values = _context6.sent;
            lagged_div = document.getElementById("dashboard-lagged");
            lagged_div = document.getElementById("dashboard-lagged");

            if (!(lagged_values === "null" || lagged_values.length === 0)) {
              _context6.next = 12;
              break;
            }

            lagged_div.appendChild(TextDiv("No lagged values available.", null, null, null, true));
            lagged_div.appendChild(space_div);
            return _context6.abrupt("return");

          case 12:
            table = document.createElement("TABLE");
            table.classList.add("default-table");
            table.classList.add("default-table-small");
            table.style.flex = "1";
            new_row = table.insertRow(-1);
            headers = [];

            if (stream.includes("z1") || stream.includes("z2") || stream.includes("z3")) {
              headers = ["Timestamp", "Z-Score"];
            } else {
              headers = ["Timestamp", "Data"];
            }

            for (_i5 = 0, _headers = headers; _i5 < _headers.length; _i5++) {
              head = _headers[_i5];
              header_cell = document.createElement("TH");
              header_cell.innerHTML = head;
              new_row.appendChild(header_cell);
            }

            i = 0;
            _iterator2 = _createForOfIteratorHelper(lagged_values);
            _context6.prev = 22;

            _iterator2.s();

          case 24:
            if ((_step2 = _iterator2.n()).done) {
              _context6.next = 36;
              break;
            }

            group = _step2.value;

            if (!(i > 50)) {
              _context6.next = 28;
              break;
            }

            return _context6.abrupt("break", 36);

          case 28:
            _new_row3 = table.insertRow(-1);
            new_cell = _new_row3.insertCell(-1);
            new_cell.appendChild(TextDiv(UnixToHMS(group[0])));
            new_cell = _new_row3.insertCell(-1);
            new_cell.appendChild(TextDiv(Round(parseFloat(group[1]), 5)));
            i = i + 1;

          case 34:
            _context6.next = 24;
            break;

          case 36:
            _context6.next = 41;
            break;

          case 38:
            _context6.prev = 38;
            _context6.t0 = _context6["catch"](22);

            _iterator2.e(_context6.t0);

          case 41:
            _context6.prev = 41;

            _iterator2.f();

            return _context6.finish(41);

          case 44:
            lagged_div.appendChild(table);

          case 45:
          case "end":
            return _context6.stop();
        }
      }
    }, _callee6, null, [[22, 38, 41, 44]]);
  }));
  return _LoadLagged.apply(this, arguments);
}

function LoadBarGraph(_x4) {
  return _LoadBarGraph.apply(this, arguments);
}

function _LoadBarGraph() {
  _LoadBarGraph = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee7(plot) {
    var graphs;
    return regeneratorRuntime.wrap(function _callee7$(_context7) {
      while (1) {
        switch (_context7.prev = _context7.next) {
          case 0:
            document.getElementById("dashboard-bargraph-container").style.display = "block";
            graphs = plot;
            Plotly.plot("dashboard-bargraph", graphs, {}, {
              responsive: true
            });

          case 3:
          case "end":
            return _context7.stop();
        }
      }
    }, _callee7);
  }));
  return _LoadBarGraph.apply(this, arguments);
}

function reLoadBarGraph(_x5) {
  return _reLoadBarGraph.apply(this, arguments);
}

function _reLoadBarGraph() {
  _reLoadBarGraph = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee8(plot) {
    var graphs;
    return regeneratorRuntime.wrap(function _callee8$(_context8) {
      while (1) {
        switch (_context8.prev = _context8.next) {
          case 0:
            document.getElementById("dashboard-bargraph-container").style.display = "block";
            graphs = plot;
            Plotly.react("dashboard-bargraph", graphs, {}, {
              responsive: true
            });

          case 3:
          case "end":
            return _context8.stop();
        }
      }
    }, _callee8);
  }));
  return _reLoadBarGraph.apply(this, arguments);
}

function LoadCDF(_x6) {
  return _LoadCDF.apply(this, arguments);
}

function _LoadCDF() {
  _LoadCDF = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee9(plot) {
    var graphs;
    return regeneratorRuntime.wrap(function _callee9$(_context9) {
      while (1) {
        switch (_context9.prev = _context9.next) {
          case 0:
            document.getElementById("dashboard-cdf-container").style.display = "inline-block";
            graphs = plot;
            Plotly.plot("dashboard-cdf", graphs, {}, {
              responsive: true
            });

          case 3:
          case "end":
            return _context9.stop();
        }
      }
    }, _callee9);
  }));
  return _LoadCDF.apply(this, arguments);
}

function LoadConStreams(_x7) {
  return _LoadConStreams.apply(this, arguments);
}

function _LoadConStreams() {
  _LoadConStreams = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee10(delays) {
    var url, request, dict;
    return regeneratorRuntime.wrap(function _callee10$(_context10) {
      while (1) {
        switch (_context10.prev = _context10.next) {
          case 0:
            url = "https://api.microprediction.org/budgets/";
            // request = new Request(url, {
            //   method: 'GET'
            // });
            _context10.next = 4;
            return Fetch(url).then(function (request) {
              return request;
            }).then(function (request) {
              globalList = request;
            });

          case 4:
            dict = _context10.sent;

          case 5:
          case "end":
            return _context10.stop();
        }
      }
    }, _callee10);
  }));
  return _LoadConStreams.apply(this, arguments);
}