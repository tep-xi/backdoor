var update_interval = 25

var acceleration = 2;
var max_speed = 20;
var move_interval_min = 2000;
var move_interval_max = 10000;
var move_radius = 24;

var blink_interval_min = 1000;
var blink_interval_max = 6000;
var blink_half_frames = 15;
var blink_update_interval = 5;

var press_dist = 6;
var press_frames = 10;
var press_update_interval = 5;

var eye_r = 5;
var mouth_r = 8;
var offset = {
  mouth : {x: 56, y: 70},
  eyes : {"left" : {x: 36, y: 58}, "right" : {x: 82, y: 58}}
};
var face_cy0 = 64;
var side_h0 = 12;

window.onload = function() {
  document.getElementById('button').style.display = "none";
  svg = document.getElementById('button-face');
  svg.style.display = "block";
  mouth = svg.getElementById('mouth');
  eyes = {left: svg.getElementById('left-eye'), right: svg.getElementById('right-eye')};
  face = svg.getElementById('top');
  side = svg.getElementById('side');

  mouth     .addEventListener( 'mousedown',  press);
  eyes.left .addEventListener( 'mousedown',  press);
  eyes.right.addEventListener( 'mousedown',  press);
  face      .addEventListener( 'mousedown',  press);
  mouth     .addEventListener('touchstart',  press, false);
  eyes.left .addEventListener('touchstart',  press, false);
  eyes.right.addEventListener('touchstart',  press, false);
  face      .addEventListener('touchstart',  press, false);
  mouth     .addEventListener(   'mouseup', submit);
  eyes.left .addEventListener(   'mouseup', submit);
  eyes.right.addEventListener(   'mouseup', submit);
  face      .addEventListener(   'mouseup', submit);
  mouth     .addEventListener(  'touchend', submit, false);
  eyes.left .addEventListener(  'touchend', submit, false);
  eyes.right.addEventListener(  'touchend', submit, false);
  face      .addEventListener(  'touchend', submit, false);

  setInterval(update, update_interval);
  blink_timer();
  move_timer();
}

var states = {
  normal : 0,
  pressed : 1,
  happy : 2
}

var state = states.normal;
var pos = {x: 0, y: 0};
var target_pos = {x: 0, y: 0};
var blink_state = 0;
var press_state = 0;
var vel = {x: 0, y: 0};

function update() {
  move();
  draw();
}

function submit() {
  state = states.happy;
  var req = new XMLHttpRequest();
  req.open('POST', '/');
  req.onload = unpress;
  req.send();
}

function press() {
  state = states.pressed;
  target_pos = {x: 0, y: 0};
  if (press_state < 1) {
    press_state += 1 / press_frames;
    setTimeout(press, press_update_interval);
  } else {
    press_state = 1;
  }
}
function unpress() {
  state = states.normal;
  if (press_state > 0) {
    press_state -= 1 / press_frames;
    setTimeout(unpress, press_update_interval);
  } else {
    press_state = 0;
  }
}

function blink_timer() {
  var t = blink_interval_min + (blink_interval_max - blink_interval_min) * Math.random();
  setTimeout(_blink_timer, t);
}
function _blink_timer() {
  blink();
  blink_timer();
}
function blink() {
  var id = setInterval(do_blink, blink_update_interval, [0]);
  setTimeout(function() {
    clearInterval(id);
    blink_state = 0;
  }, 4 * blink_half_frames * blink_update_interval);
}
function do_blink(st) {
  var n = blink_half_frames;
  if (st[0] < 2*n) {
    st[0] += 1;
    if (st[0] <= n) {
      blink_state += 1/n;
    } else {
      blink_state -= 1/n;
    }
  } else {
    blink_state = 0;
  }
}

function move_timer() {
  setTimeout(function() {
    if (state == states.normal) {
      target_pos.x = (2 * Math.random() - 1) * move_radius;
      var d = Math.sqrt(move_radius**2 - target_pos.x**2);
      target_pos.y = (2 * Math.random() - 1) * d;
    }
    move_timer();
  }, move_interval_min + (move_interval_max - move_interval_min) * Math.random());
}
function move() {
  var dx = target_pos.x - pos.x;
  var dy = target_pos.y - pos.y;
  if (dx == 0 && dy == 0) return;
  var ang = Math.atan(dy/dx);
  update_movement("x", ang);
  update_movement("y", ang);
}
function update_movement(dir, ang) {
  var d = target_pos[dir] - pos[dir];
  var v = vel[dir];
  if (Math.abs(d) <= Math.abs(v)) {
    pos[dir] = target_pos[dir];
    vel[dir] = 0;
    return;
  }
  var sgn = Math.sign(vel[dir]);
  var a = Math.sign(d) * Math.abs(acceleration * trigfn[dir](ang));
  var decd = Math.abs(decel_disp(v, a));
  if (decd > Math.abs(d - v)) {
    vel[dir] -= sgn * Math.min(Math.abs(a), Math.abs(v));
  } else {
    var smax = max_speed * Math.abs(trigfn[dir](ang));
    var vnew = Math.abs(v + a) > smax ? sgn * smax : a;
    decd = Math.abs(decel_disp(vnew, a));
    if (decd <= Math.abs(d - vnew)) {
      vel[dir] = vnew;
    }
  }
  pos[dir] += vel[dir];
}
trigfn = {x: Math.cos, y: Math.sin};
function decel_disp(v, a) {
  t = v / a;
  return -a * t**2 / 2 + v * t;
}

function draw() {
  face_cy = face_cy0 + press_state * press_dist;
  side_h = side_h0 - press_state * press_dist;
  face.setAttributeNS(null, 'cy', face_cy);
  side.setAttributeNS(null, 'y', face_cy);
  side.setAttributeNS(null, 'height', side_h);
  mouth.setAttributeNS(null, 'd', mouth_d());
  eyes. left.setAttributeNS(null, 'd', eye_d( "left"));
  eyes.right.setAttributeNS(null, 'd', eye_d("right"));
}

function mouth_d() {
  var x0 = pos.x + offset.mouth.x;
  var x1 = x0 + 2 * mouth_r;
  var y = pos.y + offset.mouth.y + press_state * press_dist;
  return "M " + x0 + " " + y
    + "A " + mouth_r + " " + mouth_r + " 0 0 0 " + x1 + " " + y;
}

function eye_d(side) {
  var off = offset.eyes[side]
  var x0 = off.x + pos.x;
  var x1 = x0 + 2 * eye_r;
  var y = off.y + pos.y + press_state * press_dist;
  if (state == states.pressed) {
    var y0 = y - eye_r;
    var y1 = y;
    var y2 = y + eye_r;
    if (side == "right") {
      var temp = x1;
      x1 = x0;
      x0 = temp;
    }
    return "M " + x0 + " " + y0 + " "
      + "L " + x1 + " " + y1 + " "
      + "L " + x0 + " " + y2 + " "
      + "L " + x1 + " " + y1 + " "
      + "L " + x0 + " " + y0;
  } else {
    var m = "M " + x0 + " " + y;
    var rs = " " + eye_r + " " + eye_r + " ";
    if (state == states.happy) {
      var a1 = "A" + rs + "0 0 1 " + x1 + " " + y;
      var a2 = "A" + rs + "0 0 0 " + x0 + " " + y;
    } else {
      var a1 = "A" + rs + "0 0 0 " + x1 + " " + y;
      var sweep = +(blink_state >= 0.5);
      var r = Math.min(5 / Math.sin(Math.acos(1 - 2 * Math.abs(blink_state - 0.5))), 9999);
      var a2 = "A " + r + " " + r + " 0 0 " + sweep + " " + x0 + " " + y;
    }
    return m + " " + a1 + " " + a2;
  }
}
