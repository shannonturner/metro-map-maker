// MetroMapMaker.js

var gridRows = 80, gridCols = 80;
var activeTool = 'look';
var activeToolOption = false;
var lastToolUsed = undefined;
var activeMap = false;
var preferredGridPixelMultiplier = 20;
var lastStrokeStyle;
var redrawOverlappingPoints = {}; // Only in use by mapDataVersion 1
var rightClicking = false;
var arrowKeys = new Set();
var dragX = false;
var dragY = false;
var clickX = false;
var clickY = false;
var hoverX = false;
var hoverY = false;
var temporaryStation = {};
var temporaryLabel = {};
var pngUrl = false;
var mapHistory = []; // A list of the last several map objects
var mapRedoHistory = [];
var MAX_UNDO_HISTORY = 100; // Will reuse this for REDO as well
var currentlyClickingAndDragging = false;
var mapLineWidth = 1
var mapLineStyle = 'solid'
// mapLineWidth and mapLineStyle handle the defaults; active are the actively-chosen options
var activeLineWidth = mapLineWidth
var activeLineStyle = mapLineStyle
var activeLineWidthStyle = mapLineWidth + '-' + mapLineStyle
var mapStationStyle = 'wmata'
var menuIsCollapsed = false
var mapSize = undefined // Not the same as gridRows/gridCols, which is the potential size; this gives the current maximum in either axis
var gridStep = 5
var rulerOn = false
var rulerOrigin = []
var moveStationOn = []

var activeMarchingAnts = false
var marchingAntsOffset = 0
var selectedPoints = []

var colorShardMap = {}

var MMMDEBUG = true
var MMMDEBUG_UNDO = false

if (typeof mapDataVersion === 'undefined') {
    var mapDataVersion = undefined
}
function compatibilityModeIndicator() {
  // Visual cue to indicate that this is in compatibility mode
  // It may be most helpful if the versions progress in ROYGBV order, with black being up to date
  if (mapDataVersion == 1) {
    // At a glance, this helps me to see whether I'm on v1 or v2
    $('.M:not(.mobile)').css({"background-color": "#bd1038"}) // red
    $('#title').css({"color": "#bd1038"})
    $('#tool-move-v1-warning').attr('style', '') // Remove the display: none
    $('#tool-select, #tool-move-selection').hide()
  } else if (mapDataVersion == 2) {
    $('.M:not(.mobile)').css({"background-color": "#df8600"}) // orange
    $('#title').css({"color": "#df8600"})
    $('#tool-move-v1-warning').attr('style', 'display: none')
    $('#tool-select, #tool-move-selection').hide()
  } else {
    $('.M:not(.mobile)').css({"background-color": "#000"})
    $('#title').css({"color": "#000"})
    $('#tool-move-v1-warning').attr('style', 'display: none')
    $('#tool-select, #tool-move-selection').show()
  }
}
compatibilityModeIndicator()

const numberKeys = ['Digit1','Digit2','Digit3','Digit4','Digit5','Digit6','Digit7','Digit8','Digit9','Digit0', 'Digit1','Digit2','Digit3','Digit4','Digit5','Digit6','Digit7','Digit8','Digit9','Digit0', 'Digit1','Digit2','Digit3','Digit4','Digit5','Digit6','Digit7','Digit8','Digit9','Digit0'] // 1-30; is set up this way to have same functionality on all keyboards
const ALLOWED_LINE_WIDTHS = [100, 75.0, 50.0, 25.0, 12.5]
const ALLOWED_LINE_STYLES = ['solid', 'dashed', 'dashed_uneven', 'dense_thin', 'dense_thick', 'dotted_dense', 'dotted', 'dotted_square', 'hollow', 'hollow_open', 'color_outline', 'wide_stripes', 'square_stripes', 'stripes']
const ALLOWED_ORIENTATIONS = [0, 45, -45, 90, -90, 135, -135, 180, 1, -1];
const ALLOWED_STYLES = ['wmata', 'rect', 'rect-round', 'circles-lg', 'circles-md', 'circles-sm', 'circles-thin', 'london']
const ALLOWED_SIZES = [80, 120, 160, 200, 240, 360]
const MAX_MAP_SIZE = ALLOWED_SIZES[ALLOWED_SIZES.length-1]

var MAX_CANVAS_SIZE = 3600
var MAX_SHARDS = 8

var lowGraphicsMode = false
var HIGH_QUAL_MAX_CANVAS_SIZE = MAX_MAP_SIZE * 10
var HIGH_QUAL_MAX_SHARDS = 8
var HIGH_QUAL_PGPM = 20

var LOW_QUAL_MAX_CANVAS_SIZE = MAX_MAP_SIZE * 8 // MAX_CANVAS_SIZE equivalent when lowGraphicsMode == true
var LOW_QUAL_MAX_SHARDS = 4
var LOW_QUAL_PGPM = 12

String.prototype.replaceAll = function(search, replacement) {
    var target = this;
    return target.replace(new RegExp(search, 'g'), replacement);
}; // String.replaceAll()

function resizeGrid(size) {
  // Change the grid size to the specified size.

  // Resize the grid and paint the map on it
  size = parseInt(size);
  gridRows = size;
  gridCols = size;

  if (mapDataVersion == 3) {
    for (var color in activeMap["points_by_color"]) {
      for (var lineWidthStyle in activeMap["points_by_color"][color]) {
        for (var x=size;x<MAX_MAP_SIZE;x++) { // Delete the x-axis outright
          if (activeMap["points_by_color"][color][lineWidthStyle][x]) {
            delete activeMap["points_by_color"][color][lineWidthStyle][x]
          }
          if (activeMap['stations'] && activeMap['stations'][x]) {
            delete activeMap['stations'][x]
          }
        }
        for (var x=0; x<size; x++) {
          for (var y=0; y<MAX_MAP_SIZE; y++) { // Handle the y-axis a little differently
            if (y >= size && activeMap["points_by_color"][color][lineWidthStyle][x] && activeMap["points_by_color"][color][lineWidthStyle][x][y]) {
              delete activeMap["points_by_color"][color][lineWidthStyle][x][y]
            }
            if (y >= size && activeMap["stations"] && activeMap["stations"][x] && activeMap["stations"][x][y]) {
              delete activeMap["stations"][x][y]
            }
          } // y
        } // x
      } // lineWidthStyle
    } // color
  } else if (mapDataVersion == 2) {
    for (var color in activeMap["points_by_color"]) {
      for (var x=size;x<MAX_MAP_SIZE;x++) { // Delete the x-axis outright
        if (activeMap["points_by_color"][color]['xys'][x]) {
          delete activeMap["points_by_color"][color]['xys'][x]
        }
        if (activeMap['stations'] && activeMap['stations'][x]) {
          delete activeMap['stations'][x]
        }
      }
      for (var x=0; x<size; x++) {
        for (var y=0; y<MAX_MAP_SIZE; y++) { // Handle the y-axis a little differently
          if (y >= size && activeMap["points_by_color"][color]['xys'][x] && activeMap["points_by_color"][color]['xys'][x][y]) {
            delete activeMap["points_by_color"][color]['xys'][x][y]
          }
          if (y >= size && activeMap["stations"] && activeMap["stations"][x] && activeMap["stations"][x][y]) {
            delete activeMap["stations"][x][y]
          }
        }
      }
    }
  } else if (mapDataVersion == 1) {
    for (var x=size;x<MAX_MAP_SIZE;x++) {
      delete activeMap[x]
    }
    for (var x=0; x<size; x++) {
      for (var y=0; y<MAX_MAP_SIZE; y++) {
        if (y >= size && activeMap[x] && activeMap[x][y]) {
          delete activeMap[x][y]
        }
      }
    }
  }

  snapCanvasToGrid() 
  drawGrid()
  lastStrokeStyle = undefined; // Prevent odd problem where snapping canvas to grid would cause lines to paint with an undefined color (singletons were unaffected)

  drawCanvas(activeMap)
} // resizeGrid(size)

function resizeCanvas(zoomDirection) {
  // By resizing the #canvas-container, this will zoom in/out on the canvas

  // Get current size of the container
  var size = $('#canvas-container').width()

  step = gridCols

  if (zoomDirection == 'out' && size >= 800) {
    size = size - step
  } else if (zoomDirection == 'in' && size <= 6400) {
    size = size + step
  } else if (!Number.isNaN(zoomDirection)) {
    size = parseInt(zoomDirection)
  }

  if (size < 800) {
    size = 800
  }
  if (size > 6400) {
    size = 6400
  }

  window.sessionStorage.setItem('zoomLevel', size)
  $('#canvas-container').width(size)
  $('#canvas-container').height(size)
} // resizeCanvas(zoomDirection)

function snapCanvasToGrid(always) {
  // Whenever the pixel width or height of the grid changes,
  // like on page load, map resize, or zoom in/out, 
  // the #metro-map-canvas size needs to be updated as well so they overlap

  // Safari struggles with performance above 3600 (even on desktop); in my tests, it barely works at all
  // Chrome can handle higher sizes easily; in my tests, 7200 was fine.
  // Increasing this improves the image sharpness at larger map sizes,
  //  because the gridPixelMultiplier gets larger

  /* HEY: You've tried SO many times to optimize canvas performance
      and have thought "the best optimization is a smaller canvas"
      but the image quality suffers SO much at smaller sizes
      and the performance gains are SO meager.
      Find gains elsewhere, they aren't to be had here!

      ^ This note was true when I had only a few canvases (all colors, stations, grid, hover),
        but is less true since 7.0 when each color got its own canvas,
        so may be worth revisiting
  */

  // Resize the canvas as needed
  var canvas = document.getElementById('metro-map-canvas');
  var canvasStations = document.getElementById('metro-map-stations-canvas');
  var canvasGrid = document.getElementById('grid-canvas')
  var canvasHover = document.getElementById('hover-canvas')
  var canvasRuler = document.getElementById('ruler-canvas')
  var colorCanvases = document.getElementById('color-canvas-container').children
  var allCanvases = [canvas, canvasStations, canvasGrid, canvasHover, canvasRuler, ...colorCanvases]

  var width = MAX_CANVAS_SIZE
  var height = MAX_CANVAS_SIZE
  if (canvas.height / gridCols != preferredGridPixelMultiplier || always) {
    // Maintain a nice, even gridPixelMultiplier so the map looks uniform at every size
    // On iPhone for Safari, canvases larger than 4096x4096 would crash, so cap it
    // Note: Now capping this at 3600x3600, which will affect maps 200x200 and above;
    //  because I noticed some highly detailed maps failed to load on iPhone for Safari
    //  with the same symptoms as before
    if (gridCols * preferredGridPixelMultiplier <= MAX_CANVAS_SIZE) {
      height = gridCols * preferredGridPixelMultiplier;
    }
    if (gridRows * preferredGridPixelMultiplier <= MAX_CANVAS_SIZE) {
      width = gridRows * preferredGridPixelMultiplier;
    }

    for (var canvas of allCanvases) {
      canvas.width = width
      canvas.height = height
    }
  } // if canvas.height / gridCols != preferredGridPixelMultiplier

  $('#canvas-container').height($('#metro-map-canvas').height());
  $('#canvas-container').width($('#metro-map-canvas').height());
} // snapCanvasToGrid()

function coordinateInColor(x, y, metroMap, color, lineWidthStyle) {
  // Returns true if this x,y coordinate exists within this oolor
  if (mapDataVersion == 3) {
    if (metroMap["points_by_color"][color] && metroMap["points_by_color"][color][lineWidthStyle] && metroMap["points_by_color"][color][lineWidthStyle][x] && metroMap["points_by_color"][color][lineWidthStyle][x][y]) {
      return true
    }
  } else if (mapDataVersion == 2) {
    if (metroMap["points_by_color"][color] && metroMap["points_by_color"][color]['xys'] && metroMap["points_by_color"][color]['xys'][x] && metroMap["points_by_color"][color]['xys'][x][y]) {
      return true
    }
  } else if (mapDataVersion == 1) {
    if (!color) {
      return getActiveLine(x, y, metroMap)
    } else {
      return getActiveLine(x, y, metroMap) == color
    }
  } // mapDataVersion
  return false
} // coordinateInColor(x, y, metroMap, color)

function getActiveLine(x, y, metroMap, returnLineWidthStyle) {
  // Given an x, y coordinate pair, return the hex code for the line you're on.
  // Use this to retrieve the line for a given point on a map.
  if (mapDataVersion == 3 && metroMap["global"]["lines"]) {
    // CONSIDER: I can avoid looping over colors and styles by keeping a v1-style
    // mapping of all of the points, like:
    // [10][20] = {"color": "bd1038", "line_width": 0.25, "line_style": "solid"}
    // ^ THIS WOULD BE AN EXCELLENT THING TO DO FOR EASE AND MAINTAINABILITY
    for (var color in metroMap["points_by_color"]) {
      for (var lineWidthStyle in metroMap["points_by_color"][color]) {
        if (coordinateInColor(x, y, metroMap, color, lineWidthStyle)) {
          if (returnLineWidthStyle) {
            return [color, lineWidthStyle]
          } else {
            return color
          }
        }
      }
    }
    return undefined
  }
  if (mapDataVersion == 2 && metroMap["global"]["lines"]) {
    for (var color in metroMap["points_by_color"]) {
      if (coordinateInColor(x, y, metroMap, color)) {
        return color
      }
    }
    return undefined
  }

  if (metroMap && metroMap[x] && metroMap[x][y] && metroMap[x][y]["line"]) {
    return metroMap[x][y]["line"];
  } 
  else if (metroMap) {
    // metroMap was passed through but there was nothing at that x,y coordinate
    return undefined;
  }
  return false;
} // getActiveLine(x, y, metroMap, returnLineWidthStyle)

function isOnOrAdjacentToStation(x, y, metroMap) {
  // Returns true if a given point is on or is adjacent to a station;
  //  used to know whether the stations canvas needs redrawing
  var coordinates = [x, y]
  for (var x1=-1; x1<2; x1++) {
    for (var y1=-1; y1<2; y1++) {
      if (x1 == 0 && y1 == 0) { continue }
      coordinates.push(x + x1)
      coordinates.push(y + y1)
    }
  }

  while (coordinates.length >= 2) {
    x = coordinates.shift()
    y = coordinates.shift()
    if (getStation(x, y, metroMap)) {
      return true
    }
  }
  return false
} // isOnOrAdjacentToStation(x, y, metroMap)

function getStation(x, y, metroMap) {
  // Given an x, y coordinate pair, return the station object
  if (metroMap && (mapDataVersion == 2 || mapDataVersion == 3) && metroMap["stations"] && metroMap["stations"][x]) {
    return metroMap["stations"][x][y]
  }

  if (metroMap && metroMap[x] && metroMap[x][y] && metroMap[x][y]["station"]) {
    return metroMap[x][y]["station"]
  }
  else if (metroMap) {
    // metroMap was passed through but there was nothing at that x,y coordinate
    return undefined
  }
  return false
} // getStation(x, y, metroMap)

function getLabel(x, y, metroMap) {
  // Given an x, y coordinate pair, return the label object
  if (metroMap && (mapDataVersion == 2 || mapDataVersion == 3) && metroMap["labels"] && metroMap["labels"][x]) {
    return metroMap["labels"][x][y]
  } else if (metroMap) {
    return undefined
  }
  return false
} // getLabel(x, y, metroMap)

function moveLineStroke(ctx, x, y, lineToX, lineToY) {
  // Used by drawPoint() to draw lines at specific points
  ctx.moveTo(x * gridPixelMultiplier, y * gridPixelMultiplier);
  ctx.lineTo(lineToX * gridPixelMultiplier, lineToY * gridPixelMultiplier);
  singleton = false;
  // return lineToX + ',' + lineToY
} // moveLineStroke(ctx, x, y, lineToX, lineToY)

function determineDarkOrLightContrast(hexcolor) {
  // Given a hexcolor, return an appropriate light-or-dark
  // contrasting color

  total = 0
  rgb = [...hexcolor.matchAll(/(\d+)/g)]
  for (var c=0;c<rgb.length;c++) {
    total += parseInt(rgb[c][0])
  }
  if (total < (127 * 3)) {
    // This is a dark color, so use white to contrast
    return '#ffffff'
  } else {
    return '#000000'
  }
}

function bindRailLineEvents() {
  // Bind the events to all of the .rail-lines
  // Needs to be done whenever a new rail line is created and on page load
  $('.rail-line').click(function() {
    // Existing Rail Line
    setActiveTool('line')
    activeToolOption = $(this).css('background-color');
    $('#tool-line').addClass('draw-rail-line')
    if (activeToolOption) {
      $('#tool-line').css({
        "background-color": activeToolOption,
        "color": determineDarkOrLightContrast(activeToolOption)
      })
    }
    if ($('#tool-flood-fill').prop('checked')) {
      floodFill(hoverX, hoverY, getActiveLine(hoverX, hoverY, activeMap, (mapDataVersion >= 3)), activeToolOption, true)
      $('#tool-line-icon-pencil').hide()
      $('#tool-line-icon-paint-bucket').show()
    } else {
      drawNewHoverIndicator()
      $('#tool-line-icon-pencil').show()
      $('#tool-line-icon-paint-bucket').hide()
    }
    $('#tool-station-options').hide();
    setMoveStationAbility(true) // turn off "Move Station"
  });  
} // bindRailLineEvents()

function makeLine(x, y, deferSave) {
  if (!isWithinSelectedPoints(x, y)) {
    return
  }
  var color = rgb2hex(activeToolOption).slice(1, 7);
  if (mapDataVersion == 1) { drawArea(x, y, activeMap, true) }
  else if (mapDataVersion >= 2) {
    var previousLineWidthStyle = getActiveLine(x, y, activeMap, true)
    if (previousLineWidthStyle) {
      var previousColor = previousLineWidthStyle[0]
      var previousLineWidthStyle = previousLineWidthStyle[1]
      if (color == previousColor && activeLineWidthStyle == previousLineWidthStyle) {
        // We can skip updating the map (and redrawing the color) if nothing's changed
        return
      } // no change
    } // previousLineWidthStyle
  } // mapDataVersion

  metroMap = updateMapObject(x, y, "line", color);
  if (!deferSave) {
    autoSave(metroMap);
  }
  if (mapDataVersion >= 2) {
    redrawCanvasForColor(color, isOnOrAdjacentToStation(x, y, activeMap), previousColor)
  } else if (mapDataVersion == 1) {
    drawArea(x, y, activeMap)
  }
} // makeLine(x, y, deferSave)

function erase(x, y, deferSaveAndDraw) {
  if (!isWithinSelectedPoints(x, y)) {
    return
  }

  // I need to check for the old line and station
  // BEFORE actually doing the erase operations
  var erasedLine = getActiveLine(x, y, activeMap);
  if (!erasedLine) {
    // Erasing nothing, there's nothing to do here
    return
  }

  if (getStation(x, y, activeMap) || getLabel(x, y, activeMap)) {
    // XXX: Labels share the stations canvas;
    // if I ever change that I'll want to have a separate
    // check for redrawLabels
    var redrawStations = true;
  } else {
    var redrawStations = false;
  }
  // NOT YET IMPLEMENTED: Check if there is a label here, and if so, redraw Labels after erasing
  if (getLabel(x, y, activeMap)) {
    var redrawLabels = true
  } else {
    var redrawLabels = false
  }
  if (erasedLine && $('#tool-flood-fill').prop('checked')) {
    floodFill(x, y, getActiveLine(x, y, activeMap, (mapDataVersion >= 3)), '')
    if (mapDataVersion >= 2 && !deferSaveAndDraw) {
      // If Flood Fill is on, we actually do always want to redraw all stations,
      //  because you might have erased the line the stations were on
      var redrawCanvasArgs = [erasedLine, true]
    } else if (mapDataVersion == 1) {
      drawCanvas(activeMap)
    }
  } else {
    activeMap = updateMapObject(x, y);
    if (mapDataVersion >= 2 && !deferSaveAndDraw) {
      var redrawCanvasArgs = [erasedLine, (redrawStations || isOnOrAdjacentToStation(x, y, activeMap))]
    } else if (mapDataVersion == 1) {
      drawArea(x, y, activeMap, erasedLine, redrawStations);
    }
  }

  if (!deferSaveAndDraw) {
    autoSave(activeMap)
    redrawCanvasForColor(...redrawCanvasArgs)
  } else {
    return redrawCanvasArgs
  }

} // erase(x, y)

function redrawCanvasForColor(color, isOnOrAdjacentToStation, previousColor) {
  var t0 = performance.now()
  var shardsRedrawn = []
  var colorsToRedraw = [color]
  if (previousColor) { colorsToRedraw.push(previousColor) }
  for (var col of colorsToRedraw) {
    // Redraw the current color's shard
    var shard = getColorShard(col)[1]
    if (shardsRedrawn.indexOf(shard) > -1) {
      // Minor optimization, but if by chance previousColor is on the same shard as color,
      //  we only have to draw that shard once
      continue
    }
    var canvas = document.getElementById('color-canvas-' + shard)
    var ctx = canvas.getContext('2d', {alpha: true})
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Then redraw all colors in that shard
    for (var shardColor of colorShardMap[shard]) {
      drawColor(shardColor, canvas)
    }
    shardsRedrawn.push(shard)
  }

  // Clear the main canvas, then draw all of the shards onto the newly-cleared canvas
  drawCanvas(false, false, true)
  var canvas = document.getElementById('metro-map-canvas');
  var ctx = canvas.getContext('2d', {alpha: true});
  for (var shard of Object.keys(colorShardMap)) {
    var canvasShard = document.getElementById('color-canvas-' + shard)
    ctx.drawImage(canvasShard, 0, 0)
  }

  // Redraw the stations canvas too, if any stations were deleted or edited nearby
  if (isOnOrAdjacentToStation) {
    drawCanvas(activeMap, true)
  }

  var t1 = performance.now()
  if (MMMDEBUG) { console.log('redrawCanvasForColor finished in ' + (t1 - t0) + 'ms') }
} // redrawCanvasForColor

function makeStation(x, y) {
  // Use a temporary station and don't write to activeMap unless it actually has data
  //  this is how to make stations with no name go away on their own now that the grid is gone
  if (moveStationOn.length == 2) {
    var swappedStation = moveStationTo(moveStationOn[0], moveStationOn[1], x, y)
    if (!swappedStation) {
      return
    }
  }

  temporaryStation = {}
  if (!getActiveLine(x, y, activeMap)) {
    // Only expand the #tool-station-options if it's actually on a line
    if (activeToolOption) {
      // If a color hasn't been chosen yet, leave the buttons full width and the options open
      $('#tool-station').removeClass('width-100')
    } else {
      // The station tool is still active
      $('#tool-station').addClass('active')
      $('#tool-line').removeClass('width-100')
      $('#tool-line').removeClass('active')
    }
    $('#tool-station-options').hide();
    drawCanvas(activeMap, true) // clear any stale station indicators
    setMoveStationAbility(true) // turn off "Move Station"
    return
  }

  $('#station-name').val('');
  $('#station-coordinates-x').val(x);
  $('#station-coordinates-y').val(y);
  var allLines = $('.rail-line');

  if (moveStationOn.length == 2) {
    // If moveStationOn has coordinates but I didn't return above,
    //  I must have clicked on a station,
    //  so I want to swap which station is active
    moveStationOn = [x, y]
  }

  $('#tool-station').addClass('width-100')

  if (!getStation(x, y, activeMap)) {
    // Create a new station
    temporaryStation = {
      "name": ""
    }

    // Set default orientation and transfer status
    $('#station-transfer').prop('checked', false);
    var lastStationOrientation = window.localStorage.getItem('metroMapStationOrientation');
    if (lastStationOrientation) {
      document.getElementById('station-name-orientation').value = lastStationOrientation;
      $('#station-name-orientation').change(); // This way, it will be saved
    } else {
      document.getElementById('station-name-orientation').value = 0;
    }
    document.getElementById('station-style').value = ''
  } // if (create new station)
  else {
    // Already has a station, so clicking again shouldn't clear the existing station but should allow you to rename it and assign lines
    if (getStation(x, y, activeMap)["name"]) {
      // This station already has a name, show it in the textfield
      var stationName = getStation(x, y, activeMap)["name"].replaceAll('_', ' ');
      $('#station-name').val(stationName);

      // Pre-check the box if this is a transfer station
      if (getStation(x, y, activeMap)["transfer"]) {
        $('#station-transfer').prop('checked', true);
      } else {
        $('#station-transfer').prop('checked', false);
      }

      // Select the correct orientation too.
      document.getElementById('station-name-orientation').value = parseInt(getStation(x, y, activeMap)["orientation"]);

      document.getElementById('station-style').value = getStation(x, y, activeMap)["style"] || ''
    } // edit named station
  } // else (edit existing station)

  // Now, there are two indicators for when a station has been placed on a line
  // and zero visual indicators for when a station gets placed on a blank square
  if (getActiveLine(x, y, activeMap)) {
    drawCanvas(activeMap, true);
    drawIndicator(x, y);
    $('#tool-station-options').show();
  }

  $('#station-name').focus(); // Set focus to the station name box to save you a click each time
} // makeStation(x, y)

function makeLabel(x, y) {
  // Modeled after makeStation,
  // use a temporary label and don't write to activeMap unless it actually has data
  temporaryLabel = {}

  // Unlike stations, labels can be placed anywhere -- even if not on a line
  $('#tool-label-options').show()

  $('#label-coordinates-x').val(x);
  $('#label-coordinates-y').val(y);

  var existingLabel = getLabel(x, y, activeMap)
  if (!existingLabel) {
    // Create a new label
    temporaryLabel = {
      "text": "",
      "shape": "",
      "text-color": "",
      "bg-color": ""
    }

    // Leave everything else the same as the most-recently used label, but clear the text.
    $('#label-text').val('')

    // Set shape to be the last-used shape;
    // everything else is too likely to change too often to be able to set defaults
    var lastLabelShape = window.localStorage.getItem('lastLabelShape')
    if (lastLabelShape) {
      document.getElementById('label-shape').value = lastLabelShape;
      $('#label-shape').trigger('change')
    }
  } else {
    // Already has a label, so populate the inputs with its current values so it can be edited

    if (existingLabel["text"]) {
      $('#label-text').val(existingLabel["text"].replaceAll('_', ' '))
    }

    if (existingLabel["shape"]) {
      $('#label-shape').val(existingLabel["shape"])
    }

    if (existingLabel["text-color"]) {
      $('#label-text-color').val(existingLabel["text-color"])
    }

    if (existingLabel["bg-color"]) {
      $('#label-bg-color').val(existingLabel["bg-color"])
    } else {
      $('#label-bg-color').hide()
      $('#label-bg-color-transparent').prop('checked', true)
    }
  } // else (label exists)

  drawCanvas(activeMap, true)
  drawLabelIndicator(x, y)

  $('#label-text').focus(); // Set focus to the label box to save you a click each time
} // makeLabel(x, y)

function bindGridSquareEvents(event) {
  if (!moveStationOn) {
    $('#station-coordinates-x').val('');
    $('#station-coordinates-y').val('');
  }

  if (!event.isTrusted) {
    // This is a click + drag
    var xy = getCanvasXY(dragX, dragY)
  } else {
    var xy = getCanvasXY(event.pageX, event.pageY)
  }
  var x = xy[0]
  var y = xy[1]

  // Straight line assist:
  // if this is a click and drag,
  // check to see if this is a straight line; otherwise return early (don't draw this)
  if (!event.isTrusted) {
    if (x == clickX || y == clickY) {
      // At least one coordinate matches, it's a straight line, do nothing
    } else if (Math.abs(x - clickX) == Math.abs(y - clickY)) {
      // Diagonal lines, do nothing
    } else {
      if ($('#straight-line-assist').prop('checked')) {
        return // Not a straight line, end early!
      }
    }
    currentlyClickingAndDragging = true
  } else {
    if (currentlyClickingAndDragging) {
      // Returning here will prevent the line from being painted outside of the guide
      //  upon mouseup after clicking + dragging,
      // but I also need to make sure we are currently clicking and dragging or
      // it would also prevent drawing a single dot
      return
    }
  }

  if (activeTool == 'line') {
    if ($('#tool-flood-fill').prop('checked')){
      var initialColor = getActiveLine(x, y, activeMap)
      var replacementColor = rgb2hex(activeToolOption).slice(1, 7);
      floodFill(x, y, getActiveLine(x, y, activeMap, (mapDataVersion >= 3)), replacementColor)
      autoSave(activeMap)
      if (mapDataVersion >= 2) {
        redrawCanvasForColor(replacementColor, isOnOrAdjacentToStation(x, y, activeMap), initialColor)
      } else if (mapDataVersion == 1) {
        drawCanvas(activeMap)
      }
    } else
      makeLine(x, y)
  } else if (activeTool == 'eraser') {
    erase(x, y)
  } else if (activeTool == 'station') {
    makeStation(x, y)
  } else if (activeTool == 'label') {
    makeLabel(x, y)
  } else if (activeTool == 'eyedropper') {
    var clws = getActiveLine(x, y, activeMap, true)
    if (clws) {
      // Click the color, and set the line width/style, too.
      if (mapDataVersion >= 3) {
        $('#rail-line-' + clws[0]).trigger('click')
        var lws = clws[1]
        activeLineWidth = lws.split('-')[0]
        activeLineStyle = lws.split('-')[1]
        activeLineWidthStyle = lws
        // This odd construction is because Javascript won't respect the zero after the decimal
        var button = $('button[data-linewidth="' + ALLOWED_LINE_WIDTHS[ALLOWED_LINE_WIDTHS.indexOf(activeLineWidth * 100)] + '"]')
        if (!button.length) {
          button = $('button[data-linewidth="' + ALLOWED_LINE_WIDTHS[ALLOWED_LINE_WIDTHS.indexOf(activeLineWidth * 100)] +'.0"]')
        }
        button.trigger('click')
        $('button[data-linestyle="' + ALLOWED_LINE_STYLES[ALLOWED_LINE_STYLES.indexOf(activeLineStyle)] + '"]').trigger('click')
      } else {
        $('#rail-line-' + clws).trigger('click')
      }
      $('#tool-eyedropper').removeClass('active')
      $('#tool-eyedropper').removeAttr('style')
    } // if color, lineWidthStyle
  } else if (activeTool == 'move' && selectedPoints.length > 0) {
    var corners = getCornersOfSelection(selectedPoints)
    var bbox2 = getPointsWithinBoundingBox(x, y, x + (corners[2] - corners[0]), y + (corners[3] - corners[1]))
    moveSelectionTo(selectedPoints, bbox2)
  }
} // bindGridSquareEvents()

function bindGridSquareMouseover(event) {
  if (MMMDEBUG) {
    // $('#title').text([event.pageX, event.pageY, getCanvasXY(event.pageX, event.pageY)])
    // $('#title').text(['XY: ' + getCanvasXY(event.pageX, event.pageY)])
  }
  $('#ruler-xy').text(getCanvasXY(event.pageX, event.pageY))
  xy = getCanvasXY(event.pageX, event.pageY)
  hoverX = xy[0]
  hoverY = xy[1]

  if (rightClicking) {
    // CONSIDER: Pan-scroll on right click
  }

  if (!mouseIsDown && activeTool == 'eyedropper') {
    var clws = getActiveLine(xy[0], xy[1], activeMap, true)
    if (clws) {
      if (mapDataVersion >= 3) {
        var color = clws[0]
      } else {
        var color = clws
      }
      $('#tool-eyedropper').css({'background-color': '#' + color, 'color': '#ffffff'})
    } else {
      $('#tool-eyedropper').removeAttr('style')
    }
  }

  if (!mouseIsDown && !$('#tool-flood-fill').prop('checked')) {
    drawHoverIndicator(event.pageX, event.pageY)
    if (rulerOn && rulerOrigin.length > 0 && (activeTool == 'look' || activeTool == 'line' || activeTool == 'eraser')) {
      drawRuler(hoverX, hoverY)
    }
  } else if (!mouseIsDown && (activeToolOption || activeTool == 'eraser') && $('#tool-flood-fill').prop('checked')) {
    if (activeTool == 'line' && activeToolOption) {
      indicatorColor = activeToolOption
    } else if (activeTool != 'line' && activeTool != 'eraser') {
      drawHoverIndicator(event.pageX, event.pageY);
      return
    } else {
      indicatorColor = '#ffffff'
    }
    floodFill(hoverX, hoverY, getActiveLine(hoverX, hoverY, activeMap, (mapDataVersion >= 3)), indicatorColor, true)
  } else if (!mouseIsDown && (activeTool != 'line' && activeTool != 'eraser') && $('#tool-flood-fill').prop('checked')) {
    drawHoverIndicator(event.pageX, event.pageY);
    return
  }
  if (mouseIsDown && (activeTool == 'line' || activeTool == 'eraser')) {
    dragX = event.pageX
    dragY = event.pageY
    $('#canvas-container').click()
  }
  if (mouseIsDown && (rulerOn && rulerOrigin.length > 0 && (activeTool == 'look' || activeTool == 'line' || activeTool == 'eraser'))) {
    drawRuler(hoverX, hoverY)
  }
  if (mouseIsDown && activeTool == 'select') {
    // Draw the marching ants preview
    drawSelectionBox(clickX, clickY, xy[0], xy[1])
  }
} // bindGridSquareMouseover()

function bindGridSquareMouseup(event) {
  // Workaround to give focus to #station-name after mousedown
  // Just don't steal focus away from another text box
  if (activeTool == 'station' && document.activeElement.type != 'text' && moveStationOn.length == 0) {
    $('#station-name').focus()
  }
  // Unset current click's x, y coordinates,
  // since we don't need to do straight line assist drawing anymore

  if (activeTool == 'select') {
    // Capture these because clickX and clickY are about to be unset
    clearMarchingAnts()
    var x1 = clickX
    var y1 = clickY
    xy = getCanvasXY(event.pageX, event.pageY)
    drawMarchingAnts(x1, y1, xy[0], xy[1])
    selectedPoints = getPointsWithinBoundingBox(x1, y1, xy[0], xy[1])
  }

  clickX = false
  clickY = false

  mouseIsDown = false
  rightClicking = false

  // Immediately clear the straight line assist indicator upon mouseup
  drawHoverIndicator(event.pageX, event.pageY)

  if (rulerOn && rulerOrigin.length > 0 && (activeTool == 'line' || activeTool == 'eraser')) {
    // Reset the rulerOrigin and clear the canvas
    rulerOrigin = []
    var canvas = document.getElementById('ruler-canvas')
    var ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)
  }
}

function bindGridSquareMousedown(event) {
  // Set the current click's x, y coordinates
  // to facilitate straight line assist drawing
  xy = getCanvasXY(event.pageX, event.pageY)
  clickX = xy[0]
  clickY = xy[1]

  if (event.button == 2) {
    // Right click
    rightClicking = true
  }

  if (activeTool == 'select') {
    clearMarchingAnts()
  }

  // Visually indicate which squares you can fill in with
  //  straight line assist
  if ($('#straight-line-assist').prop('checked') && (activeTool == 'line' || activeTool == 'eraser')) {
    // HMM: Can I optimize this so I don't need to loop over every xy? (Not a big performance concern, but might be nice if I have the time)
    for (var x=0; x<gridRows; x++) {
      for (var y=0; y<gridCols; y++) {
        if (x == clickX || y == clickY || Math.abs(x - clickX) == Math.abs(y - clickY)) {
          if (isWithinSelectedPoints(x, y)) {
            drawHoverIndicator(x, y, '#2E71CC')
          } else {
            drawHoverIndicator(x, y, '#CC2E70')
          }
        } // if it's a straight line from the origin
      } // for y
    } // for x
  } else if (!$('#straight-line-assist').prop('checked') && (activeTool == 'line' || activeTool == 'eraser') && selectedPoints.length > 0) {
    // When selectedPoints is active but the guide isn't, it's nice to have some way of showing
    // which coordinates you can/can't draw/erase
    // CONSIDER: Showing this even when the guide is active, though that's probably
    //  unnecessary since when the guide is active, you get the guide immediately at your clickXY
    var canvas = document.getElementById('hover-canvas')
    var ctx = canvas.getContext('2d')
    var inBounds = getCornersOfSelection(selectedPoints).map((n) => n * gridPixelMultiplier)
    ctx.fillStyle = '#CC2E70'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    ctx.clearRect(inBounds[0] - (gridPixelMultiplier / 2), inBounds[1] - (gridPixelMultiplier / 2), (inBounds[2] - inBounds[0]) + (gridPixelMultiplier), (inBounds[3] - inBounds[1])  + (gridPixelMultiplier))
  }// if straight line assist is checked

  if (mouseIsDown && dragX) {
    // Already clicking and dragging
  } else {
    mouseIsDown = true
    currentlyClickingAndDragging = false
  }

  if (rulerOn) {
    drawRuler(clickX, clickY, true)
  }
} // function bindGridSquareMousedown()

function drawHoverIndicator(x, y, fillColor, opacity) {
  // Displays a hover indicator on the hover canvas at x,y
  var canvas = document.getElementById('hover-canvas')
  var ctx = canvas.getContext('2d')
  var gridPixelMultiplier = canvas.width / gridCols
  if (!fillColor) {
    // Only clear the canvas if we aren't indicating straight line assist
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    // When using straight line assist, we calculate the x, y ahead of time
    xy = getCanvasXY(x, y)
    x = xy[0]
    y = xy[1]
  }
  ctx.globalAlpha = opacity || 0.5
  // Adjust hover indicator color based on active line or eraser
  if (activeTool == 'line' && activeToolOption && rgb2hex(activeToolOption))
    var activeColor = '#' + rgb2hex(activeToolOption).slice(1, 7)
  else if (activeTool == 'eraser' && !getActiveLine(x, y, activeMap))
    var activeColor = '#000000'
  else if (activeTool == 'eraser')
    var activeColor = '#ffffff'
  else if (activeTool == 'station' && moveStationOn.length == 2) {
    ctx.font = '700 ' + gridPixelMultiplier + 'px sans-serif';
    if (!getActiveLine(x, y, activeMap) || getStation(x, y, activeMap)) {
      ctx.globalAlpha = 0.25 // Visually indicate that it's not valid
    } else {
      ctx.globalAlpha = 0.75
    }
    drawStation(ctx, moveStationOn[0], moveStationOn[1], activeMap, false, x, y)
  } else if (activeTool == 'move' && selectedPoints.length > 0) {
    // CONSIDER: it may be more legible if the full station names were also part of what gets displayed,
    //  though that may add quite a bit of complexity
    var sliceCoords = getCornersOfSelection(selectedPoints).map((n) => n * gridPixelMultiplier)

    var validPlacement = true
    var selectOrigin = selectedPoints[0]

    var bbox2 = createNewBoundingBox(selectedPoints, x - selectOrigin[0], y - selectOrigin[1])
    var bboxes = getIntersectionAndDifferences(selectedPoints, bbox2)
    var intersection = bboxes[0]
    var bbox2diff1 = bboxes[2] // Determines whether this is a valid placement

    if (intersection.size == selectedPoints.length) {
      // Selections are the same, placement is valid
    }

    for (var bbxy of bbox2diff1) {
      bbxy = bbxy.split(",")
      if (validPlacement && getActiveLine(bbxy[0], bbxy[1], activeMap)) {
        // Can't move to this space if any coords
        //  in the non-overlapping portion of bbox2 has a point already
        // This is almost perfect except it counts empty space in the bounding box.
        // However, I'm not sure that's necessarily a bad thing, because
        //  if you wanted to move it again, it might be very difficult to get this point again
        //  unless/until I make the Lasso select tool
        validPlacement = false // CONSIDER: Consider showing a visual bell to indicate failure
      }
    }
    if (validPlacement) {
      ctx.globalAlpha = 0.75
    } else {
      ctx.globalAlpha = 0.25
      ctx.fillStyle = '#CC2E70'
      ctx.fillRect(
        (x * gridPixelMultiplier) - (gridPixelMultiplier / 2),
        (y * gridPixelMultiplier) - (gridPixelMultiplier / 2),
        (sliceCoords[2] - sliceCoords[0] + gridPixelMultiplier),
        (sliceCoords[3] - sliceCoords[1] + gridPixelMultiplier)
      )
    }

    // TODO: it may be possible to get better performance by defining these above and using the willreadfrequently flag -- test on a slower computer to see if it's worth it!
    // See https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/getContext#willreadfrequently for additional flags
    // May also benefit from throttling drawHoverIndicator altogether
    var mainCanvas = document.getElementById('metro-map-canvas')
    var stationCanvas = document.getElementById('metro-map-stations-canvas')

    ctx.drawImage( // image, sx, sy, sWidth, sHeight, dx, dy, dWidth, dHeight)
      mainCanvas,
      sliceCoords[0] - (gridPixelMultiplier / 2),
      sliceCoords[1] - (gridPixelMultiplier / 2),
      (sliceCoords[2] - sliceCoords[0]) + gridPixelMultiplier,
      (sliceCoords[3] - sliceCoords[1]) + gridPixelMultiplier,
      (x * gridPixelMultiplier) - (gridPixelMultiplier / 2),
      (y * gridPixelMultiplier) - (gridPixelMultiplier / 2),
      (gridPixelMultiplier, sliceCoords[2] - sliceCoords[0]) + gridPixelMultiplier,
      (gridPixelMultiplier, sliceCoords[3] - sliceCoords[1]) + gridPixelMultiplier
    )
    ctx.drawImage(
      stationCanvas,
      sliceCoords[0]  - (gridPixelMultiplier / 2),
      sliceCoords[1]  - (gridPixelMultiplier / 2),
      (sliceCoords[2] - sliceCoords[0]) + gridPixelMultiplier,
      (sliceCoords[3] - sliceCoords[1]) + gridPixelMultiplier,
      (x * gridPixelMultiplier) - (gridPixelMultiplier / 2),
      (y * gridPixelMultiplier) - (gridPixelMultiplier / 2),
      (sliceCoords[2] - sliceCoords[0]) + gridPixelMultiplier,
      (sliceCoords[3] - sliceCoords[1]) + gridPixelMultiplier
    )
  }
  ctx.fillStyle = fillColor || activeColor || '#2ECC71'
  ctx.fillRect((x * gridPixelMultiplier) - (gridPixelMultiplier / 2), (y * gridPixelMultiplier) - (gridPixelMultiplier / 2), gridPixelMultiplier, gridPixelMultiplier)
} // drawHoverIndicator(x, y)

function drawNewHoverIndicator() {
  // When changing colors via keyboard shortcuts,
  // visually indicate the newly selected color
  var canvas = document.getElementById('hover-canvas')
  var ctx = canvas.getContext('2d')
  ctx.save();
  // Draw mask to buffer
  ctx.drawImage(canvas, 0, 0, canvas.width, canvas.height, 0, 0, canvas.width, canvas.height);
  // Draw the color only where the mask exists (using source-in)
  ctx.globalAlpha = 0.75
  ctx.fillStyle = activeToolOption
  ctx.globalCompositeOperation = "source-in";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.restore();
} // drawNewHoverIndicator()

function drawGrid() {
  // Draws the gridlines on the canvas

  var canvas = document.getElementById('grid-canvas');
  var ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.globalAlpha = 0.5
  gridPixelMultiplier = canvas.width / gridCols;
  for (var x=0; x<gridCols; x++) {
    if (gridStep && x % gridStep == 0) {
      ctx.strokeStyle = '#60AEFF'
      if (x > 0) { // Ignore the first so we don't get two zeroes next to each other looking silly
        var gridX, gridY;
        // This looks fiddly, hardcoded, and complex. (Maybe so!)
        // But all it's for is to visually center the numbers so they align with the darker line
        if (gridCols <= 240) {
          gridY = gridPixelMultiplier / 2
          if (x < 10) {
            gridX = (x * gridPixelMultiplier) + (gridPixelMultiplier / 4) + 2
          } else if (x < 100) {
            gridX = (x * gridPixelMultiplier) + (gridPixelMultiplier / 4)
          } else if (x >= 100) {
            gridX = (x * gridPixelMultiplier) + (gridPixelMultiplier / 4) - 4
          }
        } else if (gridCols > 240) {
          gridY = gridPixelMultiplier / 1.25
          if (x < 10) {
            gridX = (x * gridPixelMultiplier) + (gridPixelMultiplier / 4)
          } else if (x < 100) {
            gridX = (x * gridPixelMultiplier) + (gridPixelMultiplier / 4) - 3
          } else if (x < 1000) {
            gridX = (x * gridPixelMultiplier) + (gridPixelMultiplier / 4) - 6
          }
        }
        ctx.fillText(x, gridX, gridY);
        // And at the bottom
        ctx.fillText(x, gridX, (canvas.height - (gridPixelMultiplier / 4)));
      }
    } else {
      ctx.strokeStyle = '#80CEFF'
    }
    ctx.beginPath()
    ctx.moveTo((x * gridPixelMultiplier) + (gridPixelMultiplier / 2), 0);
    ctx.lineTo((x * gridPixelMultiplier) + (gridPixelMultiplier / 2), canvas.height);
    ctx.stroke()
    ctx.closePath()
  }
  for (var y=0; y<gridRows; y++) {
    if (gridStep && y % gridStep == 0) {
      ctx.strokeStyle = '#60AEFF'
      ctx.fillText(y, 0, (y * gridPixelMultiplier) + (gridPixelMultiplier / 2) + 3);
      // And at the right
      var gridMarkOffset = ctx.measureText(y)
      if (y > 0) { // Don't show the first 0 on the right side
        ctx.fillText(y, (canvas.width - gridMarkOffset.width - (gridPixelMultiplier / 4)), (y * gridPixelMultiplier) + (gridPixelMultiplier / 2) + 3);
      }
    } else {
      ctx.strokeStyle = '#80CEFF'
    }
    ctx.beginPath()
    ctx.moveTo(0, (y * gridPixelMultiplier) + (gridPixelMultiplier / 2));
    ctx.lineTo(canvas.width, (y * gridPixelMultiplier) + (gridPixelMultiplier / 2));
    ctx.stroke()
    ctx.closePath()
  }
  if (!gridStep) {
    $('#grid-step').text('off')
  } else {
    $('#grid-step').text(gridStep)
  }
} // drawGrid()

function getRedrawSection(x, y, metroMap, redrawRadius) {
  // Returns an object that's a subset of metroMap
  // containing only the squares within redrawRadius of x,y
  redrawSection = {}
  redrawRadius = parseInt(redrawRadius)
  for (var nx=redrawRadius * -1; nx<=redrawRadius; nx+=1) {
    for (var ny=redrawRadius * -1; ny<=redrawRadius; ny+=1) {
      if (getActiveLine(x + nx, y + ny, metroMap)) {
        if (!redrawSection.hasOwnProperty(x + nx)) {
          redrawSection[x + nx] = {}
          redrawSection[x + nx][y + ny] = true;
        } else {
          redrawSection[x + nx][y + ny] = true;
        }
      }
    } // for ny
  } // for nx
  return redrawSection;
} // getRedrawSection(x, y, metroMap, redrawRadius)

function drawArea(x, y, metroMap, erasedLine, redrawStations) {
  // Partially draw an area centered on x,y
  // because it's faster than drawing the full canvas

  var canvas = document.getElementById('metro-map-canvas');
  var ctx = canvas.getContext('2d', {alpha: false});
  gridPixelMultiplier = canvas.width / gridCols;
  fontSize = gridPixelMultiplier

  var redrawRadius = 1;

  x = parseInt(x);
  y = parseInt(y);

  // ctx.lineWidth = gridPixelMultiplier * mapLineWidth;
  ctx.lineWidth = gridPixelMultiplier * activeLineWidth;
  ctx.lineCap = 'round';

  if (activeTool == 'eraser') {
    if (erasedLine) {
      drawPoint(ctx, x, y, metroMap, erasedLine);
    } // if erasedLine
  } // if activeTool == 'eraser'

  // Determine redraw area and redraw the points that need to be redrawn
  redrawSection = getRedrawSection(x, y, metroMap, redrawRadius);
  for (var x in redrawSection) {
    for (var y in redrawSection[x]) {
      lastStrokeStyle = undefined; // I need to set lastStrokeStyle here, otherwise drawPoint() has undefined behavior
      x = parseInt(x);
      y = parseInt(y);
      if (activeTool == 'line' && erasedLine) {
        // When drawing lines, we call drawArea() twice.
        // First call: erase all the squares in the redrawSection
        // Second call: re-draw all the squares
        drawPoint(ctx, x, y, metroMap, getActiveLine(x,y, metroMap));
      } else {
        drawPoint(ctx, x, y, metroMap);
      } // else (of if activeTool is line and first pass)
    } // for y
  } // for x

  if (redrawSection && !redrawStations) {
    // For when I need to maybe redraw some stations but not all stations
    var canvasStations = document.getElementById('metro-map-stations-canvas');
    var ctxStations = canvasStations.getContext('2d', {alpha: true});
    // Importantly, we're not calling clearRect here!
    ctxStations.font = '700 ' + fontSize + 'px sans-serif';

    for (var x in redrawSection) {
      for (var y in redrawSection[x]) {
        x = parseInt(x);
        y = parseInt(y);
        drawStation(ctxStations, x, y, metroMap, true)
        drawLabel(ctxStations, x, y, metroMap)
      } // for y
    } // for x
  } else if (redrawStations) {
    // Did I erase a station? Re-draw them all here
    var canvasStations = document.getElementById('metro-map-stations-canvas');
    var ctxStations = canvasStations.getContext('2d', {alpha: true});
    ctxStations.clearRect(0, 0, canvasStations.width, canvasStations.height);
    ctxStations.font = '700 ' + fontSize + 'px sans-serif';

    if (mapDataVersion == 2 || mapDataVersion == 3) {
      for (var x in metroMap['stations']) {
        for (var y in metroMap['stations'][x]) {
          x = parseInt(x);
          y = parseInt(y);
          drawStation(ctxStations, x, y, metroMap);
        } // for y
      } // for x
      // XXX: As long as I'm re-using the metro-map-stations-canvas
      // for the labels, I'll need to re-draw them here.
      // (That might be reason enough to not re-use the canvas!)
      for (var x in metroMap['labels']) {
        for (var y in metroMap['labels'][x]) {
          x = parseInt(x)
          y = parseInt(y)
          drawLabel(ctxStations, x, y, metroMap)
        } // for y
      } // for x
    } // mapDataVersion (2, 3)
    else if (mapDataVersion == 1) {
      for (var x in metroMap) {
        for (var y in metroMap[x]) {
          x = parseInt(x);
          y = parseInt(y);
          if (!Number.isInteger(x) || !Number.isInteger(y)) {
            continue;
          }
          drawStation(ctxStations, x, y, metroMap);
        } // for y
      } // for x
    } // mapDataVersion
  } // if redrawStations
} // drawArea(x, y, metroMap, redrawStations)

function drawColor(color, canvas) {
  // Draws only a single color
  if (!color) {
    // When flood filling on an empty area, the initial color is undefined,
    //  so end here -- there's nothing to do.
    return
  }
  if (!canvas) {
    var canvas = getColorShard(color)[0]
  }
  var ctx = canvas.getContext('2d', {alpha: true})
  if (mapDataVersion == 3) {
    for (var lineWidthStyle in activeMap['points_by_color'][color]) {
      ctx.strokeStyle = '#' + color
      var thisLineWidth = lineWidthStyle.split('-')[0] * gridPixelMultiplier
      var thisLineStyle = lineWidthStyle.split('-')[1]
      var linesAndSingletons = findLines(color, lineWidthStyle)
      var lines = linesAndSingletons["lines"]
      var singletons = linesAndSingletons["singletons"]
      for (var line of lines) {
        if (thisLineStyle == 'wide_stripes' || thisLineStyle == 'square_stripes' || thisLineStyle == 'stripes') {
          // Draw the hollow line first
          if (thisLineStyle == 'wide_stripes') {
            ctx.lineCap = 'square'
          } else {
            ctx.lineCap = 'butt'
          }
          ctx.lineWidth = thisLineWidth
          ctx.setLineDash([])
          ctx.beginPath()
          moveLineStroke(ctx, line[0], line[1], line[2], line[3])
          ctx.stroke()
          ctx.closePath()

          // Draw the mask at 75% size
          ctx.save()
          ctx.globalCompositeOperation = 'xor';
          ctx.lineWidth = thisLineWidth * 0.75
          ctx.beginPath()
          moveLineStroke(ctx, line[0], line[1], line[2], line[3])
          ctx.stroke()
          ctx.clip()
          ctx.restore()
        }

        // vvv Drawing the line itself vvv
        ctx.beginPath()
        ctx.lineWidth = thisLineWidth
        setLineStyle(thisLineStyle, ctx)
        moveLineStroke(ctx, line[0], line[1], line[2], line[3])
        ctx.stroke()
        ctx.closePath()
        // ^^^ Drawing the line itself ^^^

        if (thisLineStyle == 'hollow_round' || thisLineStyle == 'hollow' || thisLineStyle == 'hollow_open' || thisLineStyle == 'color_outline') {
          // The hollow portion actually gets drawn after the regular line
          ctx.save()
          if (thisLineStyle == 'color_outline') {
            ctx.globalCompositeOperation = 'screen'
          } else {
            ctx.globalCompositeOperation = 'xor';
          }
          ctx.lineWidth = Math.ceil((gridPixelMultiplier * 3 / 5) * (thisLineWidth / gridPixelMultiplier))
          ctx.beginPath()
          moveLineStroke(ctx, line[0], line[1], line[2], line[3])
          ctx.stroke()
          ctx.clip()
          ctx.restore()
        }
      }
      for (var s of singletons) {
        var xy = s.split(',')
        var x = xy[0]
        var y = xy[1]
        ctx.strokeStyle = '#' + color
        drawPoint(ctx, x, y, activeMap, false, color, (thisLineWidth / gridPixelMultiplier), thisLineStyle)
      }
    } // lineWidthStyle
  } else if (mapDataVersion == 2) {
    ctx.strokeStyle = '#' + color
    if (activeMap && activeMap['global'] && activeMap['global']['style']) {
      ctx.lineWidth = (activeMap['global']['style']['mapLineWidth'] || 1) * gridPixelMultiplier
    } else {
      ctx.lineWidth = mapLineWidth * gridPixelMultiplier
    }
    ctx.lineCap = 'round';
    var linesAndSingletons = findLines(color)
    var lines = linesAndSingletons["lines"]
    var singletons = linesAndSingletons["singletons"]
    for (var line of lines) {
      ctx.beginPath()
      moveLineStroke(ctx, line[0], line[1], line[2], line[3])
      ctx.stroke()
      ctx.closePath()
    }
    for (var s of singletons) {
      var xy = s.split(',')
      var x = xy[0]
      var y = xy[1]
      ctx.strokeStyle = '#' + color
      drawPoint(ctx, x, y, activeMap, false, color)
    } // singletons
  } // mapDataVersion
} // drawColor(ctx, color)

function getColorShard(color) {
  // Return the canvas this color belongs to,
  //  and update colorShardMap
  var shardNumber = Object.keys(activeMap["global"]["lines"]).sort().indexOf(color) % document.getElementsByClassName('color-canvas').length
  var canvas = document.getElementById('color-canvas-' + shardNumber)
  if (!colorShardMap[shardNumber]) {
    colorShardMap[shardNumber] = new Set()
  }
  colorShardMap[shardNumber].add(color)
  return [canvas, shardNumber]
}

function setColorShardMap() {
  for (var color of Object.keys(activeMap["global"]["lines"]).sort()) {
    // This is lazy, and I don't love a function named "get" being the one that sets the thing,
    //   but it has the advantage of always being in sync with getColorShard,
    //   so I think it's worth it.
    getColorShard(color)
  }
}

function findLines(color, lineWidthStyle) {
  // JS implementation of mapdata_optimizer.find_lines

  if (mapDataVersion == 2 && !lineWidthStyle) {
    // 'xys' isn't the width or style, but this avoids repeating essentially the same code
    // and keeps the functions compatible between mapDataVersion 2 and 3
    lineWidthStyle = 'xys'
  } 

  if ((mapDataVersion == 2 || mapDataVersion == 3) && (!activeMap || !activeMap['points_by_color'] || !activeMap['points_by_color'][color] || !activeMap['points_by_color'][color][lineWidthStyle])) {
    return
  }

  var directions = ['E', 'S', 'NE', 'SE']
  var skipPoints = {
    "E": new Set(),
    "S": new Set(),
    "NE": new Set(),
    "SE": new Set()
  }

  var lines = []
  var singletons = new Set()
  var notSingletons = new Set()

  for (var direction of directions) {
    for (var x in activeMap['points_by_color'][color][lineWidthStyle]) {
      for (var y in activeMap['points_by_color'][color][lineWidthStyle][x]) {
        var point = x + ',' + y
        if (skipPoints[direction].has(point)) {
          continue
        }
        var endpoint = findEndpointOfLine(x, y, activeMap['points_by_color'][color][lineWidthStyle], direction)
        if (endpoint) {
          lines.push([parseInt(x), parseInt(y), endpoint['x1'], endpoint['y1']])
          notSingletons.add(point)
          notSingletons.add(endpoint['x1'] + ',' + endpoint['y1'])
          for (var pt of endpoint['between']) {
            notSingletons.add(pt)
            skipPoints[direction].add(pt)
          }
        } else if (notSingletons.has(point)) {
          // This might not make a line in this direction,
          // but it does make a line in SOME direction,
          // so it's not a singleton
        } else {
          singletons.add(point)
        } // if endpoint/not singleton/else
      } // for y
    } // for x
  } // for directions

  // COMPATIBILITY: singletons.difference(notSingletons)
  // is not supported on Edge, Firefox
  if (typeof singletons.difference == 'function') {
    var finalSingletons = singletons.difference(notSingletons)
  } else {
    var finalSingletons = new Set()
    for (var s of singletons) {
      if (!notSingletons.has(s)) {
        // This point is not in the set of points that are connected to others.
        // In other words, it's confirmed to be a singleton
        finalSingletons.add(s)
      }
    }
  } // singletons.difference check

  return {
    "lines": lines,
    "singletons": finalSingletons
  }
} // findLines(color)

function findEndpointOfLine(x, y, pointsThisColor, direction) {
  // JS implementation of mapdata_optimizer.find_endpoint_of_line
  var between = [x + ',' + y]

  directions = {
      'E': {'dx': 1, 'dy': 0},
      'S': {'dx': 0, 'dy': 1},
      'NE': {'dx': 1, 'dy': -1},
      'SE': {'dx': 1, 'dy': 1},
      'SW': {'dx': -1, 'dy': 1},
  }

  var dx = directions[direction]['dx']
  var dy = directions[direction]['dy']
  var x1 = parseInt(x) + dx
  var y1 = parseInt(y) + dy

  if (!pointsThisColor || !pointsThisColor[x] || !pointsThisColor[x][y]) {
    return
  }

  if (!pointsThisColor[x1] || !pointsThisColor[x1][y1]) {
    return
  }

  while (pointsThisColor[x1] && pointsThisColor[x1][y1]) {
    between.push(x1 + ',' + y1)
    var x1 = parseInt(x1) + dx
    var y1 = parseInt(y1) + dy
  }

  var xy = between[between.length-1].split(',')
  x1 = parseInt(xy[0])
  y1 = parseInt(xy[1])

  return {
    "between": between,
    "x1": x1,
    "y1": y1
  }
} // findEndpointOfLine(x, y, pointsThisColor, direction)

function drawCanvas(metroMap, stationsOnly, clearOnly) {
  t0 = performance.now();
  // Fully redraw the canvas based on the provided metroMap;
  //    if no metroMap is provided, then save the existing grid as a metroMap object
  //    then redraw the canvas
  if (stationsOnly) {
    // If I'm only changing the stations, I only need to update the stations canvas
  } else {
  var canvas = document.getElementById('metro-map-canvas');
  var ctx = canvas.getContext('2d', {alpha: false});

  // How much larger is the canvas than the grid has in squares?
  // If the grid has 80x80 squares and the canvas is 1600x1600,
  //    then the gridPixelMultiplier is 20 (1600 / 80)
  gridPixelMultiplier = Math.floor(canvas.width / gridCols)
  var fontSize = gridPixelMultiplier

  // Clear the canvas, make the background white instead of transparent
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  if (clearOnly) {
    return
  }

  if (!metroMap) {
    metroMap = activeMap
  }
  activeMap = metroMap;

  ctx.lineWidth = mapLineWidth * gridPixelMultiplier
  ctx.lineCap = 'round';

  if (mapDataVersion >= 2) {
    // IMPORTANT NOTE: If I ever stop fully resetting the colorShardMap here,
    //  I'll need to do it when adding/editing/removing lines
    colorShardMap = new Object()
    setColorShardMap()
    for (var shardCanvas of document.getElementsByClassName('color-canvas')) {
        var shard = shardCanvas.id.split('-')[2]
        if (!colorShardMap[shard]) {
          continue // Nothing at this shard yet
        }
        // Clear this shard, then draw all of its colors
        var shardCanvasCtx = shardCanvas.getContext('2d', {alpha: true});
        shardCanvasCtx.clearRect(0, 0, shardCanvas.width, shardCanvas.height);
        for (var shardColor of colorShardMap[shard]) {
          drawColor(shardColor, shardCanvas)
      }
      ctx.drawImage(shardCanvas, 0, 0)
    }
  } else if (mapDataVersion == 1) {
    for (var x in metroMap) {
      for (var y in metroMap[x]) {
        x = parseInt(x);
        y = parseInt(y);
        if (!Number.isInteger(x) || !Number.isInteger(y)) {
          continue;
        }
        drawPoint(ctx, x, y, metroMap);
      }
    }
    // Redraw select overlapping points
    // This solves the "Southeast" problem
    //  where if two adjacent lines were heading southeast, they would overlap
    //  in ways that didn't happen for two adjacent lines heading northeast
    var reversed = Object.keys(redrawOverlappingPoints).reverse();
    for (var i=0; i<reversed.length; i++) {
      var x = reversed[i];
      for (var y in redrawOverlappingPoints[x]) {
        x = parseInt(x);
        y = parseInt(y);
        drawPoint(ctx, x, y, metroMap);
      }
    }
    redrawOverlappingPoints = {};
  } // mapType/dataVersion check
  } // else (of if stationsOnly)
  // Draw the stations separately, or they will be painted over by the lines themselves.
  var canvas = document.getElementById('metro-map-stations-canvas');
  var ctx = canvas.getContext('2d', {alpha: true});
  gridPixelMultiplier = Math.floor(canvas.width / gridCols) // This looks like it's redundant with above; it's not! Don't delete this.
  var fontSize = gridPixelMultiplier
  ctx.font = '700 ' + fontSize + 'px sans-serif';

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (mapDataVersion == 3 || mapDataVersion == 2) {
    for (var x in metroMap['stations']) {
      for (var y in metroMap['stations'][x]) {
        x = parseInt(x);
        y = parseInt(y);
        drawStation(ctx, x, y, metroMap)
      }
    } // stations
    for (var x in metroMap['labels']) {
      for (var y in metroMap['labels'][x]) {
        x = parseInt(x)
        y = parseInt(y)
        // Currently, labels are drawn on the stations canvas.
        // There's no reason that they couldn't have their own canvas,
        // but it seems fine to re-use the stations canvas.
        drawLabel(ctx, x, y, metroMap)
      }
    } // labels
  } else if (mapDataVersion == 1) {
  for (var x in metroMap){
    for (var y in metroMap[x]) {
      x = parseInt(x);
      y = parseInt(y);
      if (!Number.isInteger(x) || !Number.isInteger(y)) {
        continue;
      }
      drawStation(ctx, x, y, metroMap);
    } // for y
  } // for x
  } // mapType/dataVersion check

  // Add a map credit to help promote the site
  ctx.textAlign = 'start'
  ctx.font = '700 ' + fontSize + 'px sans-serif';
  ctx.fillStyle = '#000000';
  var mapCredit = 'Created with MetroMapMaker.com';
  var textWidth = ctx.measureText(mapCredit).width;
  ctx.fillText(mapCredit, (gridRows * gridPixelMultiplier) - textWidth, (gridCols * gridPixelMultiplier) - 50);

  // Has a shareable link been created for this map? If so, add it to the corner
  var shareableLink = document.getElementById('shareable-map-link');
  if (shareableLink) {
    shareableLink = shareableLink.text;
    if (shareableLink.length > 0 && shareableLink.slice(0, 26) == "https://metromapmaker.com/") {
      var remixCredit = 'Remix this map! Go to ' + shareableLink;
      var textWidth = ctx.measureText(remixCredit).width;
      ctx.fillText(remixCredit, (gridRows * gridPixelMultiplier) - textWidth, (gridCols * gridPixelMultiplier) - 25);
    }
  }
  t1 = performance.now();
  if (MMMDEBUG) { console.log('drawCanvas(map, ' + stationsOnly + ', ' + clearOnly + ') finished in ' + (t1 - t0) + 'ms') }
} // drawCanvas(metroMap, stationsOnly, clearOnly)

function drawPoint(ctx, x, y, metroMap, erasedLine, color, lineWidth, lineStyle) {
  // Draw a single point at position x, y

  x = parseInt(x)
  y = parseInt(y)

  var color = color || getActiveLine(x, y, metroMap)
  if (!color && activeTool != 'eraser') {
    return // Fixes bug where clearing a map and resizing would sometimes paint undefined spots
  }

  ctx.beginPath()

  if (!lastStrokeStyle || lastStrokeStyle != color) {
    // Making state changes to the canvas is expensive
    // So only change it if there is no lastStrokeStyle,
    // or if the lastStrokeStyle doesn't match the activeLine
    ctx.strokeStyle = '#' + color;
    lastStrokeStyle = color;
  }

  if (erasedLine) {
    // Repurpose drawPoint() for erasing; use in drawArea()
    ctx.strokeStyle = '#ffffff';
    color = erasedLine;
  }
  else {
    // CONSIDER: There's a display bug if I accidentally call drawPoint with lineWidth set
    //  where it includes the gridPixelMultiplier already; may be worth clamping it to a maximum value,
    //  or only allowing one of ALLOWED_LINE_WIDTHS during the call
    ctx.lineWidth = (gridPixelMultiplier * (lineWidth || activeLineWidth))
    setLineStyle(lineStyle || activeLineStyle, ctx)
  }

  singleton = true;

  if (lineWidth && lineStyle) {
    var thisLineWidthStyle = lineWidth + '-' + lineStyle
  } else {
    var thisLineWidthStyle = activeLineWidthStyle
  }

  // Diagonals
  if (coordinateInColor(x + 1, y + 1, metroMap, color, thisLineWidthStyle)) {
    // Direction: SE
    moveLineStroke(ctx, x, y, x+1, y+1)
    // If this southeast line is adjacent to a different color on its east,
    //  redraw these overlapping points later
    if (!redrawOverlappingPoints[x]) {
      redrawOverlappingPoints[x] = {}
    }
    redrawOverlappingPoints[x][y] = true
  } if (coordinateInColor(x - 1, y - 1, metroMap, color, thisLineWidthStyle)) {
    // Direction: NW
    // Since the drawing goes left -> right, top -> bottom,
    //  I don't need to draw NW if I've drawn SE
    //  I used to cut down on calls to getActiveLine() and moveLineStroke()
    //  by just directly setting/getting singleton.
    // But now that I'm using drawPoint() inside of drawArea(),
    // I can't rely on this shortcut anymore. (only a problem with mapDataVersion 1)
    moveLineStroke(ctx, x, y, x-1, y-1)
  } if (coordinateInColor(x + 1, y - 1, metroMap, color, thisLineWidthStyle)) {
    // Direction: NE
    moveLineStroke(ctx, x, y, x+1, y-1)
  }  if (coordinateInColor(x - 1, y + 1, metroMap, color, thisLineWidthStyle)) {
    // Direction: SW
    moveLineStroke(ctx, x, y, x-1, y+1)
  }

  // Cardinals
  if (coordinateInColor(x + 1, y, metroMap, color, thisLineWidthStyle)) {
    // Direction: E
    moveLineStroke(ctx, x, y, x+1, y)
  } if (coordinateInColor(x - 1, y, metroMap, color, thisLineWidthStyle)) {
    // Direction: W
    moveLineStroke(ctx, x, y, x-1, y)
  } if (coordinateInColor(x, y + 1, metroMap, color, thisLineWidthStyle)) {
    // Direction: S
    moveLineStroke(ctx, x, y, x, y+1)
  } if (coordinateInColor(x, y - 1, metroMap, color, thisLineWidthStyle)) {
    // Direction: N
    moveLineStroke(ctx, x, y, x, y-1)
  }

  var thisStation = getStation(x, y, metroMap)
  if (singleton) {
    // Without this, singletons with no neighbors won't be painted at all.
    // So map legends, "under construction", or similar lines should be painted.
    if (erasedLine) {
      ctx.fillStyle = '#ffffff';
    } else {
      ctx.fillStyle = '#' + color;
    }

    if (mapStationStyle == 'rect' || (thisStation && thisStation['style'] == 'rect')) {
        ctx.fillRect((x - 0.5) * gridPixelMultiplier, (y - 0.5) * gridPixelMultiplier, gridPixelMultiplier, gridPixelMultiplier)
    } else if (mapStationStyle == 'circles-md' || (thisStation && thisStation['style'] == 'circles-md')) {
      ctx.arc(x * gridPixelMultiplier, y * gridPixelMultiplier, gridPixelMultiplier * .7, 0, Math.PI * 2, true);
      ctx.fill();
    } else if (mapStationStyle == 'circles-sm' || (thisStation && thisStation['style'] == 'circles-sm')) {
      ctx.arc(x * gridPixelMultiplier, y * gridPixelMultiplier, gridPixelMultiplier * .5, 0, Math.PI * 2, true);
      ctx.fill();
    } else {
      ctx.arc(x * gridPixelMultiplier, y * gridPixelMultiplier, gridPixelMultiplier * .9, 0, Math.PI * 2, true); // Rail-line circle
      ctx.fill();
    }
  } else {
    // Doing one stroke at the end once all the lines are known
    //  rather than several strokes will improve performance
    ctx.stroke()
  } // singleton

  ctx.closePath()
} // drawPoint(ctx, x, y, metroMap)

function drawStation(ctx, x, y, metroMap, skipText, drawAtX, drawAtY) {
  var station = getStation(x, y, metroMap)
  if (station) {
    var isTransferStation = station["transfer"];
  } else {
    return; // If it's not a station, I can end here.
  }
  var isMoving = false

  // The original (x, y) values if I'm replacing them with (drawAtX, drawAtY) below
  var stationX = x
  var stationY = y
  if (drawAtX !== undefined && drawAtY !== undefined) {
    // Used to get the real station from above, but draw it somewhere else.
    //  which is nice when hovering.
    x = drawAtX
    y = drawAtY
    isMoving = true
  }

  var thisStationStyle = station["style"] || mapStationStyle
  var drawAsConnected = false
  var lineDirection = false

  if (!thisStationStyle || thisStationStyle == 'wmata') {
    drawStyledStation_WMATA(ctx, x, y, metroMap, isTransferStation)
  } else if (thisStationStyle == 'circles-lg') {
    var thisStationColor = '#' + getActiveLine(x, y, metroMap)
    drawStyledStation_WMATA(ctx, x, y, metroMap, isTransferStation, thisStationColor)
  } else if (thisStationStyle == 'circles-md') {
    drawCircleStation(ctx, x, y, metroMap, isTransferStation, 0.3, gridPixelMultiplier / 2)
  } else if (thisStationStyle == 'circles-sm') {
    drawCircleStation(ctx, x, y, metroMap, isTransferStation, 0.25, gridPixelMultiplier / 4)
  } else if (thisStationStyle == 'rect') {
    drawAsConnected = drawStyledStation_rectangles(ctx, x, y, metroMap, station, isTransferStation, 0, 0, false, false, isMoving)
  } else if (thisStationStyle == 'rect-round' || thisStationStyle == 'circles-thin') {
    drawAsConnected = drawStyledStation_rectangles(ctx, x, y, metroMap, station, isTransferStation, 0, 0, 20, false, isMoving)
  } else if (thisStationStyle == 'london') {
    var stationNameOffset = drawStyledStation_London(ctx, x, y, metroMap, station, false, false, isMoving)
    // Based on the station orientation and whether it's an xfer station,
    //  modify the drawAtX and drawAtY values very slightly from x, y
    //  to subtly offset where the name is drawn
    if (stationNameOffset && stationNameOffset.length > 0 && !drawAtX && !drawAtY) {
      if (stationNameOffset.length == 2) {
        drawAtX = x + stationNameOffset[0]
        drawAtY = y + stationNameOffset[1]
      } else if (stationNameOffset == 'endcap') {
        // Kinda hacky patch to make endcaps "borrow" the spacing of transfer stations; consider refactoring
        isTransferStation = true
      }
    }
  }

  if (!skipText) {
    drawStationName(ctx, stationX, stationY, metroMap, station, isTransferStation, drawAsConnected, drawAtX, drawAtY)
  }
} // drawStation(ctx, x, y, metroMap)

function drawStationName(ctx, x, y, metroMap, station, isTransferStation, drawAsConnected, drawAtX, drawAtY) {
  // Write the station name
  ctx.textAlign = 'start'
  ctx.fillStyle = '#000000';
  ctx.save();
  var stationName = station["name"].replaceAll('_', ' ')
  var orientation = parseInt(station["orientation"])
  var textSize = ctx.measureText(stationName).width;

  if (drawAtX !== undefined && drawAtY !== undefined) {
    x = drawAtX
    y = drawAtY
  }

  if (isTransferStation)
    var xOffset = gridPixelMultiplier * 1.5
  else if (drawAsConnected)
    var xOffset = gridPixelMultiplier
  else
    var xOffset = gridPixelMultiplier * .75
  var yOffset = gridPixelMultiplier * .25

  // Rotate the canvas if specified in the station name orientation
  if (orientation == -45) {
    ctx.translate(x * gridPixelMultiplier, y * gridPixelMultiplier);
    ctx.rotate(-45 * (Math.PI/ 180));
    ctx.fillText(stationName, xOffset, yOffset);
  } else if (orientation == 45) {
    ctx.translate(x * gridPixelMultiplier, y * gridPixelMultiplier);
    ctx.rotate(45 * (Math.PI/ 180));
    ctx.fillText(stationName, xOffset, yOffset);
  } else if (orientation == -90) {
    ctx.translate(x * gridPixelMultiplier, y * gridPixelMultiplier);
    ctx.rotate(-90 * (Math.PI/ 180));
    ctx.fillText(stationName, -1 * textSize - xOffset, yOffset);
  } else if (orientation == 90) {
    ctx.translate(x * gridPixelMultiplier, y * gridPixelMultiplier);
    ctx.rotate(-90 * (Math.PI/ 180));
    ctx.fillText(stationName, xOffset, yOffset);
  } else if (orientation == 135) {
    ctx.translate(x * gridPixelMultiplier, y * gridPixelMultiplier);
    ctx.rotate(-45 * (Math.PI/ 180));
    ctx.fillText(stationName, -1 * textSize - xOffset, yOffset);
  } else if (orientation == -135) {
    ctx.translate(x * gridPixelMultiplier, y * gridPixelMultiplier);
    ctx.rotate(45 * (Math.PI/ 180));
    ctx.fillText(stationName, -1 * textSize - xOffset, yOffset);
  } else if (orientation == 180) {
    // When drawing on the left, this isn't very different from drawing on the right
    //      with no rotation, except that we include the measured text width
    if (isTransferStation) {
      ctx.fillText(stationName, (x * gridPixelMultiplier) - (gridPixelMultiplier * 1.5) - textSize, (y * gridPixelMultiplier) + gridPixelMultiplier / 4);
    } else {
      ctx.fillText(stationName, (x * gridPixelMultiplier) - (gridPixelMultiplier) - textSize, (y * gridPixelMultiplier) + gridPixelMultiplier / 4);
    }
  } else if (orientation == 1) { // Above
    ctx.textAlign = 'center'
    if (isTransferStation) {
      ctx.fillText(stationName, (x * gridPixelMultiplier), ((y - 1.5) * gridPixelMultiplier))
    } else {
      ctx.fillText(stationName, (x * gridPixelMultiplier), ((y - 1) * gridPixelMultiplier))
    }
  } else if (orientation == -1) { // Below
    ctx.textAlign = 'center'
    if (isTransferStation) {
      ctx.fillText(stationName, (x * gridPixelMultiplier), ((y + 2.25) * gridPixelMultiplier))
    } else {
      ctx.fillText(stationName, (x * gridPixelMultiplier), ((y + 1.75) * gridPixelMultiplier))
    }
  } else  {
    if (isTransferStation) {
      ctx.fillText(stationName, (x * gridPixelMultiplier) + (gridPixelMultiplier * 1.5), (y * gridPixelMultiplier) + gridPixelMultiplier / 4);
    } else {
      ctx.fillText(stationName, (x * gridPixelMultiplier) + gridPixelMultiplier, (y * gridPixelMultiplier) + gridPixelMultiplier / 4);
    }
  } // else (of if station orientation is -45)

  ctx.restore();
}

function drawStyledStation_WMATA(ctx, x, y, metroMap, isTransferStation, outerColor, innerColor) {
  if (!outerColor) { outerColor = '#000000' }
  if (!innerColor) { innerColor = '#ffffff' }

  if (isTransferStation) {
    // Outer circle
    drawCircleStation(ctx, x, y, metroMap, isTransferStation, 1.2, 0, outerColor, 0, true)
    drawCircleStation(ctx, x, y, metroMap, isTransferStation, 0.9, 0, innerColor, 0, true)
  }

  drawCircleStation(ctx, x, y, metroMap, isTransferStation, 0.6, 0, outerColor, 0, true)
  drawCircleStation(ctx, x, y, metroMap, isTransferStation, 0.3, 0, innerColor, 0, true)
}

function drawCircleStation(ctx, x, y, metroMap, isTransferStation, stationCircleSize, lineWidth, fillStyle, strokeStyle, skipStroke) {
  if (isTransferStation && !fillStyle) {
    fillStyle = '#' + getActiveLine(x, y, metroMap) // Looks a lot nicer than filled with #000
  }
  if (!strokeStyle && isTransferStation && mapLineWidth >= 0.5) {
    strokeStyle = '#ffffff'
    lineWidth = gridPixelMultiplier / 2
  }
  ctx.fillStyle = fillStyle || '#ffffff';
  ctx.beginPath();
  ctx.arc(x * gridPixelMultiplier, y * gridPixelMultiplier, gridPixelMultiplier * stationCircleSize, 0, Math.PI * 2, true);
  ctx.closePath();
  if (!skipStroke) {
    ctx.lineWidth = lineWidth
    ctx.strokeStyle = strokeStyle || '#' + getActiveLine(x, y, metroMap)
    ctx.stroke()
  }
  ctx.fill();
}

function drawStyledStation_rectangles(ctx, x, y, metroMap, thisStation, isTransferStation, strokeColor, fillColor, radius, isIndicator, isMoving) {
  var lineColorWidthStyle = getActiveLine(x, y, metroMap, true)
  if (!lineColorWidthStyle && isMoving) {
    // Moving off a line, which isn't valid, but we want to preview
    lineColorWidthStyle = ['bd1038', '1-solid']
  }
  if (mapDataVersion == 3) {
    var lineColor = '#' + lineColorWidthStyle[0]
    var lineWidth = lineColorWidthStyle[1].split('-')[0]
  } else if (mapDataVersion == 2) {
    var lineColor = '#' + lineColorWidthStyle
    var lineWidth = mapLineWidth
  } else if (mapDataVersion == 1) {
    var lineColor = '#' + lineColorWidthStyle
    var lineWidth = 1
  }
  var lineDirection = getLineDirection(x, y, metroMap)["direction"]
  if (!lineDirection && isMoving) {
    lineDirection = 'singleton'
  }

  var rectArgs = []
  var drawAsConnected = false
  var connectedStations = getConnectedStations(x, y, metroMap)

  var width = gridPixelMultiplier
  var height = gridPixelMultiplier

  if (lineWidth >= 0.5 && lineDirection != 'singleton') {
    // If the lines are thick and this POINT isn't a singleton,
    //  the rectangles should be black/white so they can be legible
    ctx.strokeStyle = '#000000'
    ctx.fillStyle = '#ffffff'
  } else if (lineDirection == 'singleton' && (mapStationStyle == 'rect-round' || thisStation && thisStation['style'] == 'rect-round')) {
    // A singleton POINT with a rect-round singleton station looks nice in black/white too.
    ctx.strokeStyle = '#000000'
    ctx.fillStyle = '#ffffff'
  } else {
    ctx.strokeStyle = lineColor
    ctx.fillStyle = lineColor
  }

  if (connectedStations === true) {
    // Not eligible for connecting, draw as normal
    width = gridPixelMultiplier / 2
  } else if (thisStation && connectedStations && connectedStations != 'singleton' && connectedStations != 'conflicting') {
    // Connect these stations
    // set rectSize (w, h) based on the x1, y1
    dx = connectedStations.x1 - connectedStations.x0
    dy = connectedStations.y1 - connectedStations.y0
    width = (Math.abs(dx) + 1) * gridPixelMultiplier
    height = (Math.abs(dy) + 1) * gridPixelMultiplier
    drawAsConnected = true

    if (dx > 0 && dy == 0) {
      // This is a horizontally-connected station,
      // the colors can't be relied on because
      // getLineDirection() returns the direction for lines drawn with the same color
      lineDirection = 'horizontal'
    } else if (dx == 0 && dy > 0) {
      lineDirection = 'vertical'
    } else if (dx > 0 && dy > 0) {
      // Line is going NE, station should be drawn SE
      // XXX: At one point this was diagonal-se and it worked,
      // then I made a lot of changes and now diagonal-se is wrong
      // Seems odd to me that both this and the next case use diagonal-ne
      lineDirection = 'diagonal-ne'
      width = gridPixelMultiplier
    } else if (dx > 0 && dy < 0) {
      // Line is going SE, station should be drawn NE
      lineDirection = 'diagonal-ne'
      height = gridPixelMultiplier
    }
  } else if (!connectedStations && !isIndicator && !isMoving) {
    // Eligible for connecting, but it's an interior station.
    // Don't draw this station.
    return
  } else if (connectedStations == 'singleton') {
    // Use the width set via lineDirection == 'singleton',
    // and draw as normal
    if (lineDirection == 'singleton') {
      // Keep original width
      ctx.strokeStyle = '#000000'
      if (lineWidth < 0.5 && (mapStationStyle == 'rect-round' || thisStation && thisStation['style'] == 'rect-round')) {
        ctx.fillStyle = lineColor
      }
    } else if (!isTransferStation) {
      width = gridPixelMultiplier / 2
    }
  } else if (isMoving && !isTransferStation && lineDirection != 'singleton') {
    width = gridPixelMultiplier / 2
  }

  if (drawAsConnected && !isIndicator) {
    // While the all-color rounds look nice, it doesn't for multicolor
    ctx.strokeStyle = '#000000'
    ctx.fillStyle = '#ffffff'
  }

  if (!drawAsConnected || (!thisStation && isIndicator) ) {
    // If it's not a station yet but it's an indicator,
    // or if we're not drawing a connected station,
    if (mapStationStyle == 'rect-round' || (thisStation && thisStation['style'] == 'rect-round')) {
      radius = 2
    }
  }

  if (thisStation && thisStation['style'] == 'rect') {
    radius = false
  }

  function drawDiagonalRectStation(offset, orientation) {
    ctx.save()
    ctx.translate(x * gridPixelMultiplier, y * gridPixelMultiplier)
    ctx.rotate(orientation)

    // Looks great at stationSpans of 2-9 and less good above that
    if (drawAsConnected && width > height) {
      var stationSpan = (width / gridPixelMultiplier)
      if (stationSpan < 4)
        width += (stationSpan * (gridPixelMultiplier / 4))
      else
        width += (stationSpan * (gridPixelMultiplier / 3))
    } else if (drawAsConnected && height > width) {
      var stationSpan = (height / gridPixelMultiplier)
      if (stationSpan < 4)
        height += (stationSpan * (gridPixelMultiplier / 4))
      else
        height += (stationSpan * (gridPixelMultiplier / 3))
    }

    if (MMMDEBUG && x == $('#station-coordinates-x').val() && y == $('#station-coordinates-y').val())
      console.log(`stationSpan: ${stationSpan}, w1: ${width} h1: ${height}`)

    if (radius) {
      primitiveRoundRect(ctx, ...offset, width, height, radius)
    } else {
      ctx.strokeRect(...offset, width, height)
      ctx.fillRect(...offset, width, height)
    }
    ctx.restore()
  }

  if (isTransferStation) {
    ctx.lineWidth = gridPixelMultiplier / 2
  } else {
    ctx.lineWidth = gridPixelMultiplier / 4
  }

  if (isIndicator && connectedStations === false) {
    // Internal station
    if (width > height) { width = height }
    drawAsConnected = true // It's an internal station, draw the indicator in the center.
  }

  if (connectedStations == 'conflicting') {
    // There's a station to the N, W, NW, or SW,
    // but a different station in the other directions as well.
    // Draw this as a singleton, otherwise it won't get drawn at all.
    lineDirection = 'singleton'
    if (width > height) { width = height }
    drawAsConnected = false
  }

  // Override useful for drawing station indicators
  if (strokeColor) { ctx.strokeStyle = strokeColor }
  if (fillColor) { ctx.fillStyle = fillColor }

  if (MMMDEBUG && x == $('#station-coordinates-x').val() && y == $('#station-coordinates-y').val())
      console.log(`xy: ${x},${y}; wh: ${width},${height} xf: ${isTransferStation} ld: ${lineDirection} ra: ${rectArgs} cs: ${connectedStations} dac: ${drawAsConnected} sC: ${strokeColor} fC: ${fillColor}`)
  
  if (!drawAsConnected && ((mapStationStyle == 'circles-thin' && thisStation && !thisStation['style']) || (thisStation && thisStation['style'] == 'circles-thin'))) {
    if (!isIndicator) {
      strokeColor = '#000000'
      fillColor = '#ffffff'
    }
    drawCircleStation(ctx, x, y, activeMap, isTransferStation, .5, ctx.lineWidth, fillColor, strokeColor)
    return
  }

  if (lineDirection == 'singleton' || (!thisStation && isIndicator && (lineDirection == 'horizontal' || lineDirection == 'vertical'))) {
    rectArgs = [(x - 0.5) * gridPixelMultiplier, (y - 0.5) * gridPixelMultiplier, width, height]
  } else if (lineDirection == 'horizontal' && (drawAsConnected || isTransferStation)) {
    rectArgs = [(x - 0.5) * gridPixelMultiplier, (y - 0.5) * gridPixelMultiplier, width, height]
  } else if (lineDirection == 'horizontal' && !drawAsConnected) {
    rectArgs = [(x - 0.25) * gridPixelMultiplier, (y - 0.5) * gridPixelMultiplier, width, height]
  } else if (lineDirection == 'vertical' && (drawAsConnected || isTransferStation)) {
    rectArgs = [(x - 0.5) * gridPixelMultiplier, (y - 0.5) * gridPixelMultiplier, width, height]
  } else if (lineDirection == 'vertical' && !drawAsConnected) {
    rectArgs = [(x - 0.5) * gridPixelMultiplier, (y - 0.25) * gridPixelMultiplier, height, width]
  } else if (lineDirection == 'diagonal-ne' && (drawAsConnected || isTransferStation)) {
    drawDiagonalRectStation([-0.5 * gridPixelMultiplier, -0.5 * gridPixelMultiplier], Math.PI / -4)
    return
  } else if (lineDirection == 'diagonal-ne' && !drawAsConnected) {
    drawDiagonalRectStation([-0.25 * gridPixelMultiplier, -0.5 * gridPixelMultiplier], Math.PI / -4)
    return
  } else if (lineDirection == 'diagonal-se' && (drawAsConnected || isTransferStation)) {
    drawDiagonalRectStation([-0.5 * gridPixelMultiplier, -0.5 * gridPixelMultiplier], Math.PI / 4)
    return
  } else if (lineDirection == 'diagonal-se' && !drawAsConnected) {
    drawDiagonalRectStation([-0.25 * gridPixelMultiplier, -0.5 * gridPixelMultiplier], Math.PI / 4)
    return
  }

  if (radius) {
    // Unfortunately, performance on three separate calls
    //  (.roundRect, .stroke, .fill) is ABYSMAL,
    //  and there's no .strokeRoundRect or .fillRoundRect
    // .roundRect() seems new and not-yet optimized,
    //  but .rect() + .stroke() + .fill() suffers from the same issue.
    // Thankfully, assembling it via primitives is very performant
    primitiveRoundRect(ctx, ...rectArgs, radius)
  } else {
    ctx.strokeRect(...rectArgs)
    ctx.fillRect(...rectArgs)
  } // radius?

  return drawAsConnected
} // drawStyledStation_rectangles

function primitiveRoundRect(ctx, x, y, width, height, radius) {
  // ctx.roundRect exists now but has abysmal performance,
  //  but this is very performant
  if (width < 2 * radius) { radius = width / 2 }
  if (height < 2 * radius) { radius = height / 2 }
  ctx.beginPath()
  ctx.moveTo(x + radius, y)
  ctx.arcTo(x + width, y, x + width, y + height, radius)
  ctx.arcTo(x + width, y + height, x, y + height, radius)
  ctx.arcTo(x, y + height, x, y, radius)
  ctx.arcTo(x, y, x + width, y, radius)
  ctx.stroke()
  ctx.fill()
  ctx.closePath()
}

function drawStyledStation_London(ctx, x, y, metroMap, station, strokeColor, fillColor, isMoving) {
  var lineColorWidthStyle = getActiveLine(x, y, metroMap, true)
  if (!lineColorWidthStyle && isMoving) {
    // Moving off a line, which isn't valid, but we want to preview
    // BUG (Minor display): when moving a station off an existing line,
    //  this will show as a red station marker on the hover canvas
    //  on the last valid mouse position, even though the cursor is elsewhere.
    //  Curiously / a clue: this only shows for vertical and horizontal lines,
    //    and not for diagonal lines.
    lineColorWidthStyle = ['bd1038', '1-solid']
  }
  if (mapDataVersion == 3) {
    var lineColor = '#' + lineColorWidthStyle[0]
    var lineWidth = lineColorWidthStyle[1].split('-')[0]
  } else if (mapDataVersion == 2) {
    var lineColor = '#' + lineColorWidthStyle
    var lineWidth = mapLineWidth
  } else if (mapDataVersion == 1) {
    var lineColor = '#' + lineColorWidthStyle
    var lineWidth = 1
  }
  var lineDirection = getLineDirection(x, y, metroMap)
  var isDiagonal = (lineDirection["direction"] && lineDirection["direction"].indexOf('diagonal') > -1)
  var isEndcap = lineDirection["endcap"]
  if (station) {
    var markerDirection = station["orientation"]
  } else {
    var markerDirection = parseInt(window.localStorage.getItem('metroMapStationOrientation'))
  }

  // This adds a lot of complexity, but we need to adjust per line width as well,
  //   otherwise stations placed on thicker lines don't look very good.
  var height = gridPixelMultiplier / 2
  var width = gridPixelMultiplier * 0.75
  var markerOffset = 0.75
  var markerMainSizeOffset = 1
  if (lineWidth == 1) {
    height = height * 1.5
    markerMainSizeOffset = 2
    width = width * markerMainSizeOffset
    markerOffset = 1.5
  } else if (lineWidth == 0.75) {
    height = height * 1.25
    markerMainSizeOffset = 1.5
    width = width * markerMainSizeOffset
    markerOffset = 1.25
  }

  ctx.strokeStyle = strokeColor || lineColor
  ctx.fillStyle = fillColor || lineColor
  var isIndicator = !!(strokeColor && fillColor)
  ctx.lineWidth = 2

  if ((station && station["transfer"]) || lineDirection['direction'] == 'singleton') {
    // Transfer stations are drawn as a thicker black and white circle.
    ctx.strokeStyle = '#000000'
    drawCircleStation(ctx, x, y, activeMap, true, .5, gridPixelMultiplier / 4, ctx.strokeStyle, ctx.strokeStyle)
    if (isIndicator) {
      ctx.fillStyle = fillColor
    } else {
      ctx.fillStyle = '#ffffff'
    }
    drawCircleStation(ctx, x, y, activeMap, true, .4, gridPixelMultiplier / 4, ctx.fillStyle, ctx.strokeStyle, true)

    var londonConnections = getConnectedStations(x, y, activeMap, true)
    if (londonConnections && !isIndicator) {
      for (var direction in londonConnections) {
        drawLondonTransferConnection(ctx, x, y, ...londonConnections[direction])
      }
    }
  } else if (isEndcap) {
    // Non-transfer stations on an endcap are drawn as a rectangle capping that line
    var endcapMultiplier = 1.5
    if (lineWidth == 1 || lineWidth == 0.75) {
      endcapMultiplier = 1.75
    }

    width = gridPixelMultiplier * endcapMultiplier
    var xOffset = (endcapMultiplier / 6)
    var yOffset = (endcapMultiplier / 2)

    if (isDiagonal) {
      ctx.save()
      ctx.translate(x * gridPixelMultiplier, y * gridPixelMultiplier)
    }

    if (lineDirection["offset_endcap"]) {
      xOffset = (endcapMultiplier / 4)
    }

    if (lineDirection["direction"] == 'horizontal') {
      rectArgs = [(x - xOffset) * gridPixelMultiplier, (y - yOffset) * gridPixelMultiplier, height, width]
    } else if (lineDirection["direction"] == 'vertical') {
      rectArgs = [(x - yOffset) * gridPixelMultiplier, (y - xOffset) * gridPixelMultiplier, width, height]
    } else if (lineDirection["direction"] == 'diagonal-se') {
      ctx.rotate(-45 * (Math.PI / 180))
      rectArgs = [(-1 * yOffset) * gridPixelMultiplier, (-1 * xOffset) * gridPixelMultiplier, width, height]
    } else if (lineDirection["direction"] == 'diagonal-ne') {
        ctx.rotate(45 * (Math.PI / 180))
        rectArgs = [(-1 * yOffset) * gridPixelMultiplier, (-1 * xOffset) * gridPixelMultiplier, width, height]
    }

    ctx.fillRect(...rectArgs)
    ctx.strokeRect(...rectArgs)
    if (isDiagonal) {
      ctx.restore()
    }
  } else if (!station || (station && !station["transfer"])) {
    // The station name orientation for non-transfer stations also controls which side of the line the rectangular station marker appears on.
    if (isDiagonal) {
      ctx.save()
      ctx.translate(x * gridPixelMultiplier, y * gridPixelMultiplier)
    }

    if (lineDirection["direction"] == 'horizontal') {
      if ([0, -45, -135, 90, 1].indexOf(markerDirection) > -1) {
        // Draw the marker above
        rectArgs = [(x - 0.25) * gridPixelMultiplier, (y - markerOffset) * gridPixelMultiplier, height, width]
      } else if ([180, 45, 135, -90, -1].indexOf(markerDirection) > -1) {
        // Draw the marker below
        rectArgs = [(x - 0.25) * gridPixelMultiplier, (y) * gridPixelMultiplier, height, width]
      }
    } else if (lineDirection["direction"] == 'vertical') {
      if ([0, -45, 45, 90, 1].indexOf(markerDirection) > -1) {
        // Draw the marker on the right
        rectArgs = [(x) * gridPixelMultiplier, (y - 0.25) * gridPixelMultiplier, width, height]
      } else if ([180, -135, 135, -90, -1].indexOf(markerDirection) > -1) {
        // Draw the marker on the left
        rectArgs = [(x - markerOffset) * gridPixelMultiplier, (y - 0.25) * gridPixelMultiplier, width, height]
      }
    } else if (lineDirection["direction"] == 'diagonal-se') {
      if ([0, -45, 45, 90, 1].indexOf(markerDirection) > -1) {
        // Draw the marker above right
        ctx.rotate(-45 * (Math.PI / 180))
        // In rectArgs, x moves the marker left/right across the line, y moves the marker up/down the line
        rectArgs = [0, -0.25 * gridPixelMultiplier, width, height]
      } else if ([180, -135, 135, -90, -1].indexOf(markerDirection) > -1) {
        // Draw the marker below left
        ctx.rotate(-45 * (Math.PI / 180))
        rectArgs = [(-1 * markerOffset) * gridPixelMultiplier, -0.25 * gridPixelMultiplier, width, height]
      }
    } else if (lineDirection["direction"] == 'diagonal-ne') {
      if ([0, -45, 45, -90, -1].indexOf(markerDirection) > -1) {
        // Draw the marker below right
        ctx.rotate(45 * (Math.PI / 180))
        rectArgs = [0, -0.25 * gridPixelMultiplier, width, height]
      } else if ([180, -135, 135, 90, 1].indexOf(markerDirection) > -1) {
        // Draw the marker above left
        ctx.rotate(45 * (Math.PI / 180))
        rectArgs = [(-1 * markerOffset) * gridPixelMultiplier, -0.25 * gridPixelMultiplier, width, height]
      }
    }

    ctx.fillRect(...rectArgs)
    ctx.strokeRect(...rectArgs)
    if (isDiagonal) {
      ctx.restore()
    }
  } // non-transfer, non-endcap

  if (station && station['transfer']) {
    // Transfer stations already have a lot of spacing,
    //  and since the circle takes up the full grid square,
    //  we don't need special spacing.
    return []
  } else if (station && lineDirection["endcap"]) {
    return 'endcap'
  }

  var stationNameOffset = []
  if (lineDirection["direction"] == 'diagonal-se') {
    if ([-45, 45, 90, 1].indexOf(markerDirection) > -1) {
      stationNameOffset = [0.5, -0.25]
    } else if ([-135, 135, -90, -1].indexOf(markerDirection) > -1) {
      stationNameOffset = [-0.5, 0.25]
    } else if (markerDirection == 0) {
      stationNameOffset = [0.5, -0.5]
    } else if (markerDirection == 180) {
      stationNameOffset = [-0.5, 0.5]
    }

    if (lineWidth >= 0.75) {
      stationNameOffset[0] *= markerMainSizeOffset
      stationNameOffset[1] *= markerMainSizeOffset
    }
  } else if (lineDirection["direction"] == 'diagonal-ne') {
    if ([180, -135].indexOf(markerDirection) > -1) {
      stationNameOffset = [-0.25, -0.5]
    } else if ([0, 45].indexOf(markerDirection) > -1) {
      stationNameOffset = [0.25, 0.5]
    } else if ([1, 90, 135].indexOf(markerDirection) > -1) {
      stationNameOffset = [-0.5, -0.5]
    } else if ([-1, -90, -45].indexOf(markerDirection) > -1) {
      stationNameOffset = [0.5, 0.5]
    }

    if (lineWidth >= 0.75) {
      stationNameOffset[0] *= markerMainSizeOffset
      stationNameOffset[1] *= markerMainSizeOffset
    }
  } else if (lineDirection["direction"] == 'vertical') {
    if ([45, -45].indexOf(markerDirection) > -1) {
      stationNameOffset = [0.5, 0]
    } else if ([135, -135].indexOf(markerDirection) > -1) {
      stationNameOffset = [-0.5, 0]
    } else if ([1, 90].indexOf(markerDirection) > -1) {
      stationNameOffset = [0.75, 0]
    } else if ([-1, -90].indexOf(markerDirection) > -1) {
      stationNameOffset = [-0.75, 0]
    }

    if (lineWidth >= 0.75) {
      if (markerDirection == 0) {
        stationNameOffset = [0.5, 0]
      } else if (markerDirection == 180) {
        stationNameOffset = [-0.5, 0]
      }
      stationNameOffset[0] *= markerMainSizeOffset
    }
  } else if (lineDirection["direction"] == 'horizontal') {
    if ([1, 90, -135, -45].indexOf(markerDirection) > -1) {
      stationNameOffset = [0, -0.5]
    } else if ([-1, -90, 135, 45].indexOf(markerDirection) > -1) {
      stationNameOffset = [0, 0.5]
    } else if (markerDirection == 0) {
      stationNameOffset = [0, -0.75]
    } else if (markerDirection == 180) {
      stationNameOffset = [0, 0.75]
    }

    if (lineWidth >= 0.75) {
      stationNameOffset[1] *= markerMainSizeOffset
    }
  }

  return stationNameOffset
} // drawStyledStation_London

function drawLondonTransferConnection(ctx, x, y, x1, y1) {
  var dx = x - x1
  var dy = y - y1
  var xOffset = (-0.25 * dx)
  var yOffset = (-0.25 * dy)

  // Horizontal and vertical lines look better
  //  with slightly different offsets
  //  than their diagonal counterparts (which have more space to begin with)
  if (dx == 0 && Math.abs(dy) > 0) {
    // Vertical
    var yOffset = (-0.375 * dy)
  } else if (dy == 0 && Math.abs(dx) > 0) {
    // Horizontal
    var xOffset = (-0.375 * dx)
  }

  ctx.strokeStyle = '#000000'
  ctx.fillStyle = '#ffffff'

  ctx.lineWidth = gridPixelMultiplier * .525
  ctx.beginPath()
  moveLineStroke(ctx, x + xOffset, y + yOffset, x1 - xOffset, y1 - yOffset)
  ctx.stroke()

  ctx.lineWidth = gridPixelMultiplier * 0.25
  ctx.strokeStyle = '#ffffff'
  ctx.beginPath()
  moveLineStroke(ctx, x, y, x1, y1)
  ctx.stroke()
} // drawLondonTransferConnection(ctx, x, y, x1, y1)

function drawIndicator(x, y) {
  // Place a temporary station marker on the canvas;
  // this will be overwritten by the drawCanvas() call
  // but at least there will be some visual indicator of the station's placement
  // now that the grid squares aren't visible
  var canvas = document.getElementById('metro-map-stations-canvas');
  var ctx = canvas.getContext('2d', {alpha: false});
  var gridPixelMultiplier = canvas.width / gridCols;

  if (!getActiveLine(x, y, activeMap)) {
    // If there is no activeLine, don't draw any symbol.
    // Stations must be placed on a line.
    return
  }

  var permStation = getStation(x, y, activeMap)

  // Consider: refactor this further and subsume it into drawStation
  var thisStationStyle = mapStationStyle
  if (temporaryStation["style"]) {
    thisStationStyle = temporaryStation["style"]
  } else if (permStation && permStation["style"]) {
    thisStationStyle = permStation["style"]
  }

  var isTransferStation = temporaryStation["transfer"] || (permStation && permStation["transfer"])

  if (!thisStationStyle || thisStationStyle == 'wmata' || thisStationStyle == 'circles-lg') {
    drawStyledStation_WMATA(ctx, x, y, activeMap, isTransferStation, '#000000', '#00ff00')
  } else if (thisStationStyle == 'circles-md') {
    drawCircleStation(ctx, x, y, activeMap, isTransferStation, 0.3, gridPixelMultiplier / 2, '#00ff00', '#000000')
  } else if (thisStationStyle == 'circles-sm') {
    drawCircleStation(ctx, x, y, activeMap, isTransferStation, 0.25, gridPixelMultiplier / 4, '#00ff00', '#000000')
  } else if (thisStationStyle == 'rect') {
    // For this and rect-round, I don't actually want to draw the one continuous station
    //  even if I could; these all should be individually selectable.
    drawStyledStation_rectangles(ctx, x, y, activeMap, permStation, isTransferStation, '#000000', '#00ff00', false, true)
  } else if (thisStationStyle == 'rect-round' || thisStationStyle == 'circles-thin') {
    drawStyledStation_rectangles(ctx, x, y, activeMap, permStation, isTransferStation, '#000000', '#00ff00', 20, true)
  } else if (thisStationStyle == 'london') {
    drawStyledStation_London(ctx, x, y, activeMap, permStation, '#000000', '#00ff00')
  }
} // drawIndicator(x, y)

function drawLabel(ctx, x, y, metroMap, indicatorColor) {
  var label = getLabel(x, y, metroMap)

  if (!label && !indicatorColor) {
    // If there's no label here (and it's not an indicator), end
    return
  } else if (indicatorColor && !label) {
    // This is an indicator only,
    // let's see if a placeholder looks nice?
    label = {
      'text': 'Label',
      'shape': $('#label-shape').val(),
      'text-color': '#333333'
    }
  }

  var textWidth = ctx.measureText(label['text']).width
  var labelShapeWidth;
  var shapeArgs;

  if (textWidth < gridPixelMultiplier) {
    labelShapeWidth = getWidthToNearestGrid(gridPixelMultiplier * 1.25)
  } else {
    labelShapeWidth = getWidthToNearestGrid(parseInt(textWidth * 1.33))
  }
  var labelShapeHeight = gridPixelMultiplier

  // NOT YET IMPLEMENTED:
  //  Consider different font size or weight maybe
  //  Consider a different horizontal placement for the text
  //  Consider different circle sizes

  if (label["bg-color"] || indicatorColor) {
    if (indicatorColor) {
      ctx.fillStyle = indicatorColor
      ctx.strokeStyle = indicatorColor
    } else {
      ctx.fillStyle = label["bg-color"]
      ctx.strokeStyle = label["bg-color"]
    }

    if (label["shape"] == 'rect') {
      shapeArgs = [(x - 0.5) * gridPixelMultiplier, (y - 0.5) * gridPixelMultiplier, labelShapeWidth, labelShapeHeight]
      ctx.strokeRect(...shapeArgs)
      ctx.fillRect(...shapeArgs)
    } else if (label["shape"] == 'rect-round') {
      shapeArgs = [(x - 0.5) * gridPixelMultiplier, (y - 0.5) * gridPixelMultiplier, labelShapeWidth, labelShapeHeight]
      primitiveRoundRect(ctx, ...shapeArgs, 2)
    } else if (label["shape"] == 'circle') {
      shapeArgs = [x * gridPixelMultiplier, y * gridPixelMultiplier, gridPixelMultiplier, 0, Math.PI * 2]
      ctx.beginPath();
      ctx.arc(...shapeArgs);
      ctx.closePath();
      ctx.stroke()
      ctx.fill()
    } else if (label["shape"] == 'square') {
      shapeArgs = [(x - 0.5) * gridPixelMultiplier, (y - 0.5) * gridPixelMultiplier, gridPixelMultiplier, gridPixelMultiplier]
      ctx.strokeRect(...shapeArgs)
      ctx.fillRect(...shapeArgs)
    }
  } // label: bg-color; If there's no background color, there's no shape.

  if (label["text"]) {
    ctx.font = '700 ' + gridPixelMultiplier + 'px Helvetica,sans-serif';
    ctx.fillStyle = label['text-color']

    var textX, maxWidth;
    textX = (x * gridPixelMultiplier)    
    if (label["shape"] == 'circle' || label["shape"] == 'square') {
      maxWidth = gridPixelMultiplier
      ctx.textAlign = 'center'
    } else if (label["shape"] == 'oval') {
      ctx.textAlign = 'center'
    } else {
      ctx.textAlign = 'start'
    }
    ctx.fillText(label["text"], textX, (y * gridPixelMultiplier) + parseInt(gridPixelMultiplier / 3), maxWidth);
  }
} // drawLabel(ctx, x, y, metroMap)

function drawLabelIndicator(x, y) {
  // Place a temporary label marker on the canvas
  // (which is overwritten by drawCanvas later)
  var canvas = document.getElementById('metro-map-stations-canvas')
  var ctx = canvas.getContext('2d', {alpha: false})
  var gridPixelMultiplier = canvas.width / gridCols
  drawLabel(ctx, x, y, activeMap, '#00ff00')
}

function getWidthToNearestGrid(width) {
  // Returns width to the nearest gridPixelMultiplier, rounded up.
  var modulo = width % gridPixelMultiplier
  if (modulo > 0) {
    return (Math.floor(width / gridPixelMultiplier) * gridPixelMultiplier) + gridPixelMultiplier
  } else {
    return (Math.floor(width / gridPixelMultiplier) * gridPixelMultiplier)
  }
} // getWidthToNearestGrid(width)

function rgb2hex(rgb) {
    if (/^#[0-9A-F]{6}$/i.test(rgb)) return rgb;

    rgb = rgb.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
    function hex(x) {
        return ("0" + parseInt(x).toString(16)).slice(-2);
    }
    return "#" + hex(rgb[1]) + hex(rgb[2]) + hex(rgb[3]);
} // rgb2hex(rgb)

function saveMapHistory(metroMap) {
  // Add the metroMap to the history
  //  and delete the oldest once there are MAX_UNDO_HISTORY maps stored
  // Map versions are stored from Oldest -------- Newest
  if (mapHistory.length > MAX_UNDO_HISTORY) {
    mapHistory.shift(); // Remove first item in array
  }

  // IMPORTANT: this relies on window.localStorage.setItem('metroMap', metroMap)
  //  happening AFTER the call to saveMapHistory
  if (JSON.stringify(metroMap) != window.localStorage.getItem('metroMap')) {
      mapHistory.push(JSON.stringify(metroMap))
      $('span#undo-buffer-count').text('(' + mapHistory.length + ')')
      $('#tool-undo').prop('disabled', false)
  }

  debugUndoRedo()
} // saveMapHistory(metroMap)

function autoSave(metroMap) {
  // Saves the provided metroMap to localStorage
  // This should be called AFTER the event that changes the map, not before.
  if (typeof metroMap == 'object') {
    activeMap = metroMap;
    if (selectedPoints.length > 0) {
      metroMap["selectedPoints"] = structuredClone(selectedPoints)
    }
    saveMapHistory(activeMap)
    metroMap = JSON.stringify(metroMap);
  }
  window.localStorage.setItem('metroMap', metroMap); // IMPORTANT: this must happen after saveMapHistory(activeMap)
  mapRedoHistory = [] // Clear the redo buffer
  $('#tool-redo').prop('disabled', true)
  $('span#redo-buffer-count').text('')
  if (!menuIsCollapsed) {
    $('#autosave-indicator').text('Saving locally ...');
    $('#title').hide()
    setTimeout(function() {
      $('#autosave-indicator').text('');
      $('#title').show()
    }, 1500)
  }
} // autoSave(metroMap)

function loadMapFromUndoRedo(previousMap) {
  if (previousMap) {
    window.localStorage.setItem('metroMap', previousMap) // Otherwise, undoing and then loading the page before making at least 1 change will result in losing whatever changes were made since the last autoSave
    // Remove all rail lines, they'll be replaced on loadMapFromObject()
    $('.rail-line').remove();
    var previousMap = JSON.parse(previousMap)
    activeMap = previousMap
    loadMapFromObject(previousMap)
    setMapSize(previousMap, true)
    drawCanvas(previousMap)
    if ((activeTool == 'select' || activeTool == 'move') && previousMap["selectedPoints"] && previousMap["selectedPoints"].length > 0) {
      selectedPoints = previousMap["selectedPoints"]
      clearMarchingAnts()
      drawSelectionBox(...getCornersOfSelection(selectedPoints))
    } else {
      // If not using the select/move tools right now, discard the selection
      selectedPoints = []
      clearMarchingAnts()
    }
    if (previousMap['global'] && previousMap['global']['style']) {
      mapLineWidth = previousMap['global']['style']['mapLineWidth'] || mapLineWidth || 1
      mapStationStyle = previousMap['global']['style']['mapStationStyle'] || mapStationStyle || 'wmata'
    } else {
      mapLineWidth = 1
      mapStationStyle = 'wmata'
    }
    resetResizeButtons(gridCols)
    resetRailLineTooltips()
    resetStyleButtons()
    // Re-create the Edit colors drop-down menu, because the delete unused colors might have been undone/redone
    $('#tool-lines-to-change').html('<option>Edit which color?</option>')
    // Now populate the select dropdown
    for (var line in activeMap["global"]["lines"]) {
      $('#tool-lines-to-change').append('<option value="' + line + '">' + activeMap["global"]["lines"][line]["displayName"] + '</option>')
    } // for line in globals
  } // if (previousMap)
} // loadMapFromUndoRedo(previousMap)

function undo() {
  // Rewind to an earlier map in the mapHistory
  var previousMap = false
  if (mapHistory.length > 1) {
    var currentMap = mapHistory.pop(); // Remove the most recently added item in the history
    previousMap = mapHistory[mapHistory.length-1]
    $('span#undo-buffer-count').text('(' + mapHistory.length + ')')
  } else if (mapHistory.length == 1) {
    previousMap = mapHistory[0]
    $('span#undo-buffer-count').text('')
  }

  if (mapRedoHistory.length > MAX_UNDO_HISTORY) {
    mapRedoHistory.shift()
  }
  if ((currentMap || previousMap) != mapRedoHistory[mapRedoHistory.length-1]) {
    mapRedoHistory.push(currentMap || previousMap)
  } else {
    return
  }
  $('#tool-redo').prop('disabled', false)
  $('span#redo-buffer-count').text('(' + mapRedoHistory.length + ')')

  debugUndoRedo();
  loadMapFromUndoRedo(previousMap)
  $('.tooltip').hide()
} // undo()

function redo() {
  // After undoing, redo will allow you to undo the undo
  var previousMap = false
  if (mapRedoHistory.length >= 1) {
    previousMap = mapRedoHistory.pop()
    mapHistory.push(previousMap)
  } else {
    return
  }


  $('span#undo-buffer-count').text('(' + mapHistory.length + ')')
  if (!previousMap) {
    $('span#redo-buffer-count').text('')
    return
  }

  if (mapRedoHistory.length == 0) {
    $('span#redo-buffer-count').text('')
  } else {
    $('span#redo-buffer-count').text('(' + mapRedoHistory.length + ')')
  }

  loadMapFromUndoRedo(previousMap)
  $('.tooltip').hide()
} // redo()

function debugUndoRedo() {
  if (MMMDEBUG && MMMDEBUG_UNDO) {
    $('#announcement').html('')
    for (var i=0;i<mapHistory.length;i++) {
      var mhDebugMessage = i + ': ' + JSON.stringify(mapHistory[i]).length
      if (i == 0) { mhDebugMessage = mhDebugMessage + ' [OLDEST]' }
      else if (i == mapHistory.length - 1) { mhDebugMessage = mhDebugMessage + ' [NEWEST]' }
      $('#announcement').append('<p>' + mhDebugMessage + '</p>')
    }
  }
}

function getURLParameter(name) {
    return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search) || [null, ''])[1].replace(/\+/g, '%20')) || null;
}

function autoLoad() {
  // Attempts to load a saved map, in the order:
  // 1. from a URL parameter 'map' with a valid map hash
  // 2. from a map object saved in localStorage
  // 3. If neither 1 or 2, load a preset map (WMATA)
  gridStep = parseInt(window.localStorage.getItem('metroMapGridStep') || gridStep) || false
  lowGraphicsMode = window.localStorage.getItem('graphicsQualityLow') == 1 || false

  if (window.localStorage.getItem('loadingAttemptsWithoutSuccess') > 2) {
    // Attempt to catch when low graphics mode isn't enabled yet,
    //  but it should be, because loading a large map is causing an issue
    window.localStorage.setItem('graphicsQualityLow', 1)
    lowGraphicsMode = true
  } else {
    // Increment number of attempts; if we're successful, we'll set this to 0 below
    var loadingAttemptsWithoutSuccess = window.localStorage.getItem('loadingAttemptsWithoutSuccess') || 0
    window.localStorage.setItem('loadingAttemptsWithoutSuccess', loadingAttemptsWithoutSuccess + 1)
  }

  if (lowGraphicsMode) {
    MAX_CANVAS_SIZE = LOW_QUAL_MAX_CANVAS_SIZE
    MAX_SHARDS = LOW_QUAL_MAX_SHARDS
    preferredGridPixelMultiplier = LOW_QUAL_PGPM
    $('#graphics-quality-low').prop('checked', true) // Show it as already checked
    console.log(`Using low graphics mode to improve performance! MAX_CANVAS_SIZE: ${MAX_CANVAS_SIZE} MAX_SHARDS: ${MAX_SHARDS} preferredGridPixelMultiplier: ${preferredGridPixelMultiplier}`)
    var shards = document.getElementById('color-canvas-container').children
    if (shards.length > MAX_SHARDS) {
      for (var x=shards.length;x>MAX_SHARDS;x--) {
        shards[x-1].remove()
      }
    }
  }

  // Load from the savedMapData injected into the index.html template
  if (typeof savedMapData !== 'undefined') {
    activeMap = savedMapData
  } else if (window.localStorage.getItem('metroMap')) {
    // Load from local storage
    // This is a likely source of v1 mapDataVersions,
    //  so test carefully that v1 still works
    activeMap = JSON.parse(window.localStorage.getItem('metroMap'));
    if (typeof autoLoadError !== 'undefined') {
      autoLoadError = autoLoadError + 'Loading your last-edited map.'
    }
  } else {
    // If no map URLParameter and no locally stored map, default to the WMATA map
    // I think this would be more intuitive than the blank slate,
    //    and might limit the number of blank / red-squiggle maps created.
    // If the WMATA map ever changes, I'll need to update it here too.
    $.get('/load/XGQTFuVM').done(function (savedMapData) {
      activeMap = savedMapData
      if (savedMapData.replace(/\s/g,'').slice(0,7) == '[ERROR]') {
        // Fallback to an empty grid
        drawGrid()
        bindRailLineEvents()
        drawCanvas()
      } else { // Success, load the map
        activeMap = JSON.parse(activeMap)
        setMapStyle(activeMap)
        if (activeMap && activeMap['global'] && activeMap['global']['data_version']) {
          mapDataVersion = activeMap['global']['data_version']
        } else {
          mapDataVersion = 1
        }
        compatibilityModeIndicator()
        mapSize = setMapSize(activeMap, mapDataVersion > 1)
        loadMapFromObject(activeMap)
        mapHistory.push(JSON.stringify(activeMap)) // See note about saveMapHistory below
        setTimeout(function() {
          $('#tool-resize-' + gridRows).text('Initial size (' + gridRows + 'x' + gridCols + ')');
        }, 1000);
      }
    }).fail(function(err) {
      // Fallback to an empty grid
      drawGrid()
      bindRailLineEvents()
      drawCanvas()
    }).always(function() {
      upgradeMapDataVersion()
      setMapStyle(activeMap)
    })
    if (typeof autoLoadError !== 'undefined') {
      autoLoadError = autoLoadError + 'Loading the default map.'
      $('#announcement').append('<h4 id="autoLoadError" class="bg-warning" style="text-align: left;">' + autoLoadError + '</h4>')
      setTimeout(function() {
        $('#autoLoadError').remove()
      }, 3000)
    } // autoLoadError
    return
  } // else

  setMapStyle(activeMap)
  if (activeMap && activeMap['global'] && activeMap['global']['data_version']) {
    mapDataVersion = activeMap['global']['data_version']
  } else {
    mapDataVersion = 1
  }

  // Helpful for debugging / troubleshooting backwards compatibility modes
  var desiredMapDataVersion = parseInt(getURLParameter('mapDataVersion'))
  if (MMMDEBUG && desiredMapDataVersion >= mapDataVersion) {
    upgradeMapDataVersion(desiredMapDataVersion)
  } else {
    try {
      upgradeMapDataVersion()
    } catch (e) {
      console.warn('Error when trying to upgradeMapDataVersion(): ' + e)
    }
  }

  compatibilityModeIndicator()
  mapSize = setMapSize(activeMap, mapDataVersion > 1)
  loadMapFromObject(activeMap)
  // I'd prefer to use saveMapHistory() here, but
  //  that has a check to ensure that the map isn't the same as what's in
  //  localStorage, which this might be.
  mapHistory.push(JSON.stringify(activeMap))

  if (typeof autoLoadError !== 'undefined') {
    $('#announcement').append('<h4 id="autoLoadError" class="bg-warning" style="text-align: left;">' + autoLoadError + '</h4>')
    setTimeout(function() {
      $('#autoLoadError').remove()
    }, 3000)
  } // autoLoadError

  setTimeout(function() {
    $('#tool-resize-' + gridRows).text('Initial size (' + gridRows + 'x' + gridCols + ')');
  }, 1000);

  // Remember the last-used zoomLevel for this session
  var zoomLevel = window.sessionStorage.getItem('zoomLevel')
  if (zoomLevel)
    resizeCanvas(zoomLevel)

  // Successful in loading the map, reset the counter
  window.localStorage.setItem('loadingAttemptsWithoutSuccess', 0)
} // autoLoad()
autoLoad();

function getMapSize(metroMapObject) {
  // CONSIDER: Rename this as it's a bit of a misnomer,
  //  instead giving the highest x or y value in the map
  var highestValue = 0;
  if (typeof metroMapObject !== 'object') {
    metroMapObject = JSON.parse(metroMapObject);
  }

  if (mapDataVersion == 3) {
    for (var color in metroMapObject['points_by_color']) {
      for (var lineWidthStyle in metroMapObject['points_by_color'][color]) {
        thisColorHighestValue = Math.max(...Object.keys(metroMapObject['points_by_color'][color][lineWidthStyle]).map(Number).filter(Number.isInteger).filter(function (key) {
          return Object.keys(metroMapObject['points_by_color'][color][lineWidthStyle][key]).length > 0
        }))
        for (var x in metroMapObject['points_by_color'][color][lineWidthStyle]) {
          if (thisColorHighestValue >= ALLOWED_SIZES[ALLOWED_SIZES.length-2]) {
            highestValue = thisColorHighestValue
            break
          }
          // getMapSize(activeMap)
          y = Math.max(...Object.keys(metroMapObject['points_by_color'][color][lineWidthStyle][x]).map(Number).filter(Number.isInteger))
          if (y > thisColorHighestValue) {
            thisColorHighestValue = y;
          }
        } // y
        if (thisColorHighestValue > highestValue) {
          highestValue = thisColorHighestValue
        }
      } // lineWidthStyle
    } // color
  } else if (mapDataVersion == 2) {
    for (var color in metroMapObject['points_by_color']) {
        thisColorHighestValue = Math.max(...Object.keys(metroMapObject['points_by_color'][color]['xys']).map(Number).filter(Number.isInteger).filter(function (key) {
        return Object.keys(metroMapObject['points_by_color'][color]['xys'][key]).length > 0
      }))
      for (var x in metroMapObject['points_by_color'][color]['xys']) {
        if (thisColorHighestValue >= ALLOWED_SIZES[ALLOWED_SIZES.length-2]) {
          highestValue = thisColorHighestValue
          break
        }
        // getMapSize(activeMap)
        y = Math.max(...Object.keys(metroMapObject['points_by_color'][color]['xys'][x]).map(Number).filter(Number.isInteger))
        if (y > thisColorHighestValue) {
          thisColorHighestValue = y;
        }
      } // y
      if (thisColorHighestValue > highestValue) {
        highestValue = thisColorHighestValue
      }
    } // color
  } else if (mapDataVersion == 1) {
    highestValue = Math.max(...Object.keys(metroMapObject).map(Number).filter(Number.isInteger).filter(function (key) {
      return Object.keys(metroMapObject[key]).length > 0
    }))
    for (var x in metroMapObject) {
      if (highestValue >= ALLOWED_SIZES[ALLOWED_SIZES.length-2]) {
        break
      }
      y = Math.max(...Object.keys(metroMapObject[x]).map(Number).filter(Number.isInteger).filter(
        function (key) {
        return Object.keys(metroMapObject[x][key]).length > 0
      }))
      if (y > highestValue) {
        highestValue = y;
      }
    }
  }
  return highestValue
} // getMapSize(metroMapObject)

function setMapSize(metroMapObject, getFromGlobal) {
  // Sets gridRows and gridCols based on how far to the right map features have been placed
  // A map with x,y values within 0-79 will shrink to an 80x80 grid even if
  //    the grid has been extended beyond that

  var prevSize = gridRows

  if (getFromGlobal) {
    gridRows = metroMapObject['global']['map_size']
    gridCols = metroMapObject['global']['map_size']
  } else {
    highestValue = getMapSize(metroMapObject)

    for (allowedSize of ALLOWED_SIZES) {
      if (highestValue < allowedSize) {
        gridRows = allowedSize
        gridCols = allowedSize
        metroMapObject['global']['map_size'] = gridRows
        break
      }
    }
  } // if getFromGlobal/else
  
  if (prevSize > gridRows && selectedPoints.length > 0 && (selectedPoints[selectedPoints.length-1][0] > gridRows || selectedPoints[selectedPoints.length-1][1] > gridRows)) {
    // Sizing down, should clear selectedPoints if it's in the portion that's now gone
    selectedPoints = []
  }

  resizeGrid(gridRows)

  if (gridRows != prevSize) {
    // Only resize the canvas-container if the grid size changed
    // Size the canvas container to the nearest multiple of gridCols
    // #canvas-container height and width must always be the same
    $('#canvas-container').width(Math.round($('#canvas-container').width() / gridCols) * gridCols)
    $('#canvas-container').height(Math.round($('#canvas-container').width() / gridRows) * gridRows)
  }
} // setMapSize(metroMapObject)

function setMapStyle(metroMap) {
  if (metroMap && metroMap['global'] && metroMap['global']['style']) {
    mapLineWidth = metroMap['global']['style']['mapLineWidth'] || mapLineWidth
    mapStationStyle = metroMap['global']['style']['mapStationStyle'] || mapStationStyle
  }
} // setMapStyle(metroMap)

function isMapStretchable(size) {
  // Determine if the map is small enough to be stretched
  // CONSIDER: be smarter about whether I can actually stretch rather than basing it on gridRows/Cols
  if (size) {
    return size <= MAX_MAP_SIZE / 2
  } else {
    return (gridRows <= MAX_MAP_SIZE / 2 && gridCols <= MAX_MAP_SIZE / 2)
  }
}

function loadMapFromObject(metroMapObject, update) {
  // Loads a map from the provided metroMapObject and 
  //  applies the necessary styling to the grid
  if (typeof metroMapObject != 'object') {
    metroMapObject = JSON.parse(metroMapObject);
  }

  if (!update) {
    drawGrid();
    if (Object.keys(metroMapObject['global']['lines']).length > 0) {
      // Remove original rail lines if the map has its own preset rail lines
      $('#tool-line-options button.original-rail-line').remove();
    } else {
      // If there are no rail lines, load up the defaults, since that's what will show
      metroMapObject['global']['lines'] = {
        "bd1038": {"displayName":"Red Line"},
        "df8600": {"displayName":"Orange Line"},
        "f0ce15": {"displayName":"Yellow Line"},
        "00b251": {"displayName":"Green Line"},
        "0896d7": {"displayName":"Blue Line"},
        "662c90": {"displayName":"Purple Line"},
        "a2a2a2": {"displayName":"Silver Line"},
        "000000": {"displayName":"Logo"},
        "79bde9": {"displayName":"Rivers"},
        "cfe4a7": {"displayName":"Parks"}
      }
    } // else (if there are no lines in the global)

    var numLines = 1;
    for (var line in metroMapObject['global']['lines']) {
      if (metroMapObject['global']['lines'].hasOwnProperty(line) && document.getElementById('rail-line-' + line) === null) {
          if (numLines < 11) {
            keyboardShortcut = ' data-toggle="tooltip" title="Keyboard shortcut: ' + numberKeys[numLines - 1].replace('Digit', '') + '"'
          } else if (numLines < 21) {
            keyboardShortcut = ' data-toggle="tooltip" title="Keyboard shortcut: Shift + ' + numberKeys[numLines - 1].replace('Digit', '') + '"'
          } else if (numLines < 31) {
            keyboardShortcut = ' data-toggle="tooltip" title="Keyboard shortcut: Alt + ' + numberKeys[numLines - 1].replace('Digit', '') + '"'
          } else {
            keyboardShortcut = ''
          }
          $('#line-color-options fieldset #line-colors').append('<button id="rail-line-' + line + '" class="rail-line has-tooltip" style="background-color: #' + line + ';"' + keyboardShortcut + '>' + metroMapObject['global']['lines'][line]['displayName'] + '</button>');
          numLines++;
      }
    }

    $(function () {
      $('[data-toggle="tooltip"]').tooltip({"container": "body"});
      bindRailLineEvents();
      resetRailLineTooltips()
      if ($('.visible-xs').is(':visible')) {
        $('#canvas-container').removeClass('hidden-xs');
        $('#tool-export-canvas').click();
        $('#try-on-mobile').attr('disabled', false);
      } // if visible-xs && savedMapHash
    }); // Do this here because it looks like the call to this below doesn't happen in time to load all the tooltips created by the map being loaded
  } // if !update
} // loadMapFromObject(metroMapObject)

function updateMapObject(x, y, key, data) {
  // Intended to be a faster version of saveMapAsObject()
  // Instead of reconsituting the whole map object,
  //  just update what's at x,y
  // Note that when clicking and dragging, this gets called dozens of times --
  //  but it's currently so fast and performant that it isn't worth optimizing or throttling.

  if (activeMap) {
    var metroMap = activeMap;
  } else {
    // Don't request from localStorage unless we have to
    var metroMap = JSON.parse(window.localStorage.getItem('metroMap'));
  }

  if (mapDataVersion == 3 && activeTool == 'line') {
    // If the map was cleared, let's make sure we can add to it
    if (!metroMap['points_by_color'][data]) {
      metroMap['points_by_color'][data] = {}
    }

    if (!metroMap['points_by_color'][data][activeLineWidthStyle]) {
      metroMap['points_by_color'][data][activeLineWidthStyle] = {}
    }
  } else if (mapDataVersion == 2 && activeTool == 'line') {
    // If the map was cleared, let's make sure we can add to it
    if (!metroMap['points_by_color'][data] || !metroMap['points_by_color'][data]['xys']) {
      metroMap['points_by_color'][data] = {'xys': {}}
    }
  }

  if (activeTool == 'eraser') {
    if (mapDataVersion == 3) {
      if (!data) { data = getActiveLine(x, y, metroMap) }
      for (var lineWidthStyle in metroMap['points_by_color'][data]) {
        if (metroMap['points_by_color'] && metroMap['points_by_color'][data] && metroMap['points_by_color'][data][lineWidthStyle] && metroMap['points_by_color'][data][lineWidthStyle][x] && metroMap['points_by_color'][data][lineWidthStyle][x][y]) {
          delete metroMap['points_by_color'][data][lineWidthStyle][x][y]
          if (Object.values(metroMap['points_by_color'][data][lineWidthStyle][x]).filter((o) => Object.keys(o)).length == 0) {
            delete metroMap['points_by_color'][data][lineWidthStyle][x]
          }
          if (Object.values(metroMap['points_by_color'][data][lineWidthStyle]).filter((o) => Object.keys(o)).length == 0) {
            delete metroMap['points_by_color'][data][lineWidthStyle]
          }
          if (Object.values(metroMap['points_by_color'][data]).filter((o) => Object.keys(o)).length == 0) {
            delete metroMap['points_by_color'][data]
          }
        }
      }
      if (metroMap["stations"] && metroMap["stations"][x] && metroMap["stations"][x][y]) {
        delete metroMap["stations"][x][y]
      }
      if (metroMap["labels"] && metroMap["labels"][x] && metroMap["labels"][x][y]) {
        delete metroMap["labels"][x][y]
      }
    } else if (mapDataVersion == 2) {
      if (!data) { data = getActiveLine(x, y, metroMap) }
      if (metroMap['points_by_color'] && metroMap['points_by_color'][data] && metroMap['points_by_color'][data]['xys'] && metroMap['points_by_color'][data]['xys'][x] && metroMap['points_by_color'][data]['xys'][x][y]) {
        delete metroMap['points_by_color'][data]['xys'][x][y]
      }
      if (metroMap["stations"] && metroMap["stations"][x] && metroMap["stations"][x][y]) {
        delete metroMap["stations"][x][y]
      }
      if (metroMap["labels"] && metroMap["labels"][x] && metroMap["labels"][x][y]) {
        delete metroMap["labels"][x][y]
      }
    } else if (mapDataVersion == 1) {
      if (metroMap[x] && metroMap[x][y]) {
        delete metroMap[x][y]
      }
    }
    return metroMap;
  }

  // v2 & v3 is handled below, in line (with color) and station sections
  if (mapDataVersion == 1) {
    if (!metroMap.hasOwnProperty(x)) {
      metroMap[x] = {};
      metroMap[x][y] = {};
    } else {
      if (!metroMap[x].hasOwnProperty(y)) {
        metroMap[x][y] = {};
      }
    }
  }

  if (mapDataVersion == 3 && activeTool == 'line') {
    // points_by_color, data, activeLineWidthStyle were added above
    if (!metroMap['points_by_color'][data][activeLineWidthStyle][x]) {
      metroMap['points_by_color'][data][activeLineWidthStyle][x] = {}
    }
    metroMap['points_by_color'][data][activeLineWidthStyle][x][y] = 1
    // But I also need to make sure no other colors and lineWidthStyles have this x,y coordinate anymore.
    for (var color in metroMap['points_by_color']) {
      for (var lineWidthStyle in metroMap['points_by_color'][color]) {
        if (color == data && lineWidthStyle == activeLineWidthStyle) {
          continue
        }
        if (metroMap['points_by_color'][color][lineWidthStyle] && metroMap['points_by_color'][color][lineWidthStyle][x] && metroMap['points_by_color'][color][lineWidthStyle][x][y]) {
          delete metroMap['points_by_color'][color][lineWidthStyle][x][y]
        }
      } // lineWidthStyle
    } // color
  } else if (mapDataVersion == 2 && activeTool == 'line') {
    // points_by_color, data, xys were added above
    if (!metroMap['points_by_color'][data]['xys'][x]) {
      metroMap['points_by_color'][data]['xys'][x] = {}
    }
    metroMap['points_by_color'][data]['xys'][x][y] = 1
    // But I also need to make sure no other colors have this x,y coordinate anymore.
    for (var color in metroMap['points_by_color']) {
      if (color == data) {
        continue
      }
      if (metroMap['points_by_color'][color]['xys'] && metroMap['points_by_color'][color]['xys'][x] && metroMap['points_by_color'][color]['xys'][x][y]) {
        delete metroMap['points_by_color'][color]['xys'][x][y]
      }
    }
  } else if (mapDataVersion == 1 && activeTool == 'line') {
    metroMap[x][y]["line"] = data;
  } else if (activeTool == 'station') {
    if (mapDataVersion == 2 || mapDataVersion == 3) {
      if (!metroMap['stations']) {
        metroMap['stations'] = {}
      }
      if (!metroMap['stations'][x]) {
        metroMap['stations'][x] = {}
      }
      if (!metroMap['stations'][x][y]) {
        metroMap['stations'][x][y] = {}
      }
      metroMap["stations"][x][y][key] = data
    } else {
      metroMap[x][y]["station"][key] = data;
    }
  } else if (activeTool == 'label') {
    if (mapDataVersion == 2 || mapDataVersion == 3) {
      if (!metroMap['labels']) {
        metroMap['labels'] = {}
      }
      if (!metroMap['labels'][x]) {
        metroMap['labels'][x] = {}
      }
      if (!metroMap['labels'][x][y]) {
        metroMap['labels'][x][y] = {}
      }
      if (key) {
        metroMap["labels"][x][y][key] = data
      } else {
        metroMap["labels"][x][y] = data
      }
    }
  }

  return metroMap;
} // updateMapObject()

function createNewBoundingBox(bbox1, xOffset, yOffset) {
  // Use to create a temporary bounding box during hover
  //  that we can use to determine whether this is a valid placement
  var bbox2 = []
  for (var c in bbox1) {
    bbox2[c] = [bbox1[c][0] + xOffset, bbox1[c][1] + yOffset]
  }
  return bbox2
} // createNewBoundingBox(bbox1, xOffset, yOffset)

function getIntersectionAndDifferences(bbox1, bbox2) {
  // Given two bounding boxes,
  //  return the intersection (overlap)
  //  as well as all of the points from bbox1 that don't appear in bbox2
  //    (which are the ones to be deleted when moveSelectionTo occurs)
  //  and the points from bbox2 that don't appear in bbox1
  //    (which determines whether or not this is a valid placement)

  // As-is, can't get intersection/difference here like in findLines,
  //  because that uses coords in "x,y" format (as strings) rather than [x,y]
  // So let's convert it.
  var bbox1_set = new Set()
  for (var xy of bbox1) {
    bbox1_set.add(`${xy[0]},${xy[1]}`)
  }
  var bbox2_set = new Set()
  for (var xy of bbox2) {
    bbox2_set.add(`${xy[0]},${xy[1]}`)
  }

  // This would be so much easier if Javascript recognized Array equality
  if (typeof bbox1_set.difference == 'function') {
    var difference1 = bbox1_set.difference(bbox2_set)
    var difference2 = bbox2_set.difference(bbox1_set)
  } else {
    var difference1 = new Set()
    var difference2 = new Set()
    for (var c of bbox2_set) {
      if (!bbox1_set.has(c)) {
        difference1.add(c)
      }
    }
    for (var c of bbox1_set) {
      if (!bbox2_set.has(c)) {
        difference2.add(c)
      }
    }
  } // .difference compatibility check
  return [bbox1_set.intersection(bbox2_set), difference1, difference2, bbox1_set, bbox2_set]
} // getIntersectionAndDifferences(bbox1, bbox2)

function moveSelectionTo(bbox1, bbox2) {
  // Moves a selection (bbox1) to the coordinates at bbox2,
  //  if those are valid

  // CONSIDER: This is a pretty naive implementation, and could be improved upon.
  // Worth profiling to see what the performance is like, and whether there are optimizations

  var t0 = performance.now()

  var bboxes = getIntersectionAndDifferences(bbox1, bbox2)
  var intersection = bboxes[0]
  var bbox2diff1 = bboxes[2] // Determines whether this is a valid placement

  var t1 = performance.now()

  if (intersection.size == selectedPoints.length) {
    // Selections are the same, end early
    return
  }

  for (var xy of bbox2diff1) {
    xy = xy.split(",")
    if (getActiveLine(xy[0], xy[1], activeMap)) {
      // Can't move to this space if any coords
      //  in the non-overlapping portion of bbox2 has a point already
      return // CONSIDER: Consider showing a visual bell to indicate failure
    }
  }

  // Now: iterate over coords in bbox1, apply them to bbox2 coords,
  //  then delete the coords from bbox1
  //  make sure to move stations too.
  var pointsToAdd = {}
  var stationsToAdd = {}
  var newMapObject = structuredClone(activeMap)
  for (var c in bbox1) {
    var clws = getActiveLine(bbox1[c][0], bbox1[c][1], activeMap, true)
    if (!clws) { continue } // Nothing at this point
    var color = clws[0]
    var lws = clws[1]
    var xy = bbox2[c]
    var x = xy[0]
    var y = xy[1]

    // Delete the point from newMapObject
    delete newMapObject["points_by_color"][color][lws][bbox1[c][0]][bbox1[c][1]]

    // Add these after all deletes have occurred
    if (!pointsToAdd[color]) {
      pointsToAdd[color] = {}
    }
    if (!pointsToAdd[color][lws]) {
      pointsToAdd[color][lws] = {}
    }
    if (!pointsToAdd[color][lws][x]) {
      pointsToAdd[color][lws][x] = {}
    }
    pointsToAdd[color][lws][x][y] = 1

    // Delete the station if existing, too
    if (newMapObject["stations"][bbox1[c][0]] && newMapObject["stations"][bbox1[c][0]][bbox1[c][1]]) {
      delete newMapObject["stations"][bbox1[c][0]][bbox1[c][1]]
      if (Object.keys(newMapObject["stations"][bbox1[c][0]]).length == 0) {
        delete newMapObject["stations"][bbox1[c][0]]
      }

      if (!stationsToAdd[x]) {
        stationsToAdd[x] = {}
      }
      if (!stationsToAdd[x][y]) {
        stationsToAdd[x][y] = {}
      }
      stationsToAdd[x][y] = Object.assign({}, activeMap["stations"][bbox1[c][0]][bbox1[c][1]])
    }
  }

  for (var color of Object.keys(pointsToAdd)) {
    for (var lws of Object.keys(pointsToAdd[color])) {
      for (var x of Object.keys(pointsToAdd[color][lws])) {
        for (var y of Object.keys(pointsToAdd[color][lws][x])) {
          if (!newMapObject["points_by_color"][color]) {
            newMapObject["points_by_color"][color] = {}
          }
          if (!newMapObject["points_by_color"][color][lws]) {
            newMapObject["points_by_color"][color][lws] = {}
          }
          if (!newMapObject["points_by_color"][color][lws][x]) {
            newMapObject["points_by_color"][color][lws][x] = {}
          }
          newMapObject["points_by_color"][color][lws][x][y] = 1
        } // for y
      } // for x
    } // for lws
  } // for color

  // Drawing the stations
  for (var x of Object.keys(stationsToAdd)) {
    for (var y of Object.keys(stationsToAdd[x])) {
      if (!newMapObject["stations"][x]) {
        newMapObject["stations"][x] = {}
      }
      if (!newMapObject["stations"][x][y]) {
        newMapObject["stations"][x][y] = {}
      }
      newMapObject["stations"][x][y] = Object.assign({}, stationsToAdd[x][y])
    } // for y
  } // for x

  selectedPoints = bbox2
  clearMarchingAnts()
  drawSelectionBox(...getCornersOfSelection(selectedPoints))
  var t2 = performance.now()
  if (MMMDEBUG) { console.log(`PERF OF moveSelectionTo: t1-t0: ${(t1-t0)}ms t2-t1: ${t2-t1}ms`) }
  autoSave(newMapObject)
  drawCanvas(newMapObject)
} // moveSelectionTo(bbox1, bbox2)

function moveStationTo(fromX, fromY, x, y) {
  // Moves an existing station (station) to the coordinates at (x,y),
  //  if those are valid

  if (!getActiveLine(x, y, activeMap)) {
    return // CONSIDER: Consider showing visual bell to indicate failure
  }

  if (getStation(x, y, activeMap)) {
    return true // Want to swap to another station
  }

  // Set the hidden form fields station-coordinates-x, -y as well
  $('#station-coordinates-x').val(x)
  $('#station-coordinates-y').val(y)
  moveStationOn = [x, y]

  if (!activeMap['stations'][x]) {
    activeMap['stations'][x] = {}
  }
  if (!activeMap['stations'][x][y]) {
    activeMap['stations'][x][y] = {}
  }
  activeMap['stations'][x][y] = activeMap['stations'][fromX][fromY]
  delete activeMap['stations'][fromX][fromY]
  drawCanvas(activeMap, true)
  autoSave(activeMap)
} // moveStationTo(fromX, fromY, x, y)

function moveStation(directions) {
  // This is the keyboard shortcut version of moving stations;
  //  contrast with moveStationTo which is the mouse version
  if (!activeTool == 'station' && $('#tool-station-options').is(':visible')) {
    // Only allow moving a station when the station menu is open and active
    return
  }

  var xOffset = 0;
  var yOffset = 0;

  // If you hold left and right (or up/down) at the same time, it'll prefer right (down),
  //  and I guess you could say they should cancel each other out,
  //  but why would you do that?
  if (directions.has('left')) {
      var xOffset = -1;
  }
  if (directions.has('right')) {
      var xOffset = 1;
  }
  if (directions.has('up')) {
      var yOffset = -1;
  }
  if (directions.has('down')) {
      var yOffset = 1;
  }

  if (mapDataVersion == 3) {
    // moveStationTo has this check, but when mousing, I want
    //  to be able to switch which station is active,
    //  not swap positions or place one station on top of another
    if (getStation(x, y, activeMap)) {
      return // CONSIDER: Consider showing visual bell to indicate failure
    }
    var x = parseInt($('#station-coordinates-x').val())
    var y = parseInt($('#station-coordinates-y').val())
    moveStationTo(x, y, (x + xOffset), (y + yOffset))
  }
  if ($('#move-station-enabled').text().indexOf('Mouse') == -1) {
    moveStationOn = [] // Don't enable the ability to move stations with the mouse if it isn't already on
  }
  return true
} // moveStation(direction)

function moveMap(direction) {
    // Much faster and easier to read replacement
    //  of the old method of moving the map

    if (activeTool == 'station' && $('#tool-station-options').is(':visible')) {
      // Don't allow moving the map out from under a station that's actively being placed
      return
    }

    var xOffset = 0;
    var yOffset = 0;

    if (direction == 'left') {
        var xOffset = -1;
    } else if (direction == 'right') {
        var xOffset = 1;
    } else if (direction == 'down') {
        var yOffset = 1;
    } else if (direction == 'up') {
        var yOffset = -1;
    }

    if (selectedPoints.length > 0) {
      // Prevent from going out of bounds, which we don't need to do in a loop
      // Bounds-checking when no selectedPoints is done below
      // CONSIDER: Major improvement here would be to get the minimal points excluding blank spaces
      var sXYs = getCornersOfSelection(selectedPoints)
      if (sXYs[0] == 0 && direction == 'left') { return }
      else if (sXYs[1] == 0 && direction == 'up') { return }
      else if (sXYs[2] == (gridCols - 1) && direction == 'right') { return }
      else if (sXYs[3] == (gridRows - 1) && direction == 'down') { return }
    }

    if (mapDataVersion == 3) {
      var newPointsByColor = {}
      var newStations = {}
      for (var color in activeMap['points_by_color']) {
        newPointsByColor[color] = {}
        for (var lineWidthStyle in activeMap['points_by_color'][color]) {
          newPointsByColor[color][lineWidthStyle] = {}
          for (var x in activeMap['points_by_color'][color][lineWidthStyle]) {
            for (var y in activeMap['points_by_color'][color][lineWidthStyle][x]) {
              x = parseInt(x);
              y = parseInt(y);
              var skipDrawing = false;
              if (!Number.isInteger(x) || !Number.isInteger(y)) {
                continue;
              }
              var outsideSelection = false

              // For performance, don't bother checking points that are out of the boundaries
              if (selectedPoints.length > 0 && (x < sXYs[0] || x > sXYs[2] || y < sXYs[1] || y > sXYs[3])) {
                outsideSelection = true
              }

              if (!newPointsByColor[color][lineWidthStyle][x + xOffset]) {
                  newPointsByColor[color][lineWidthStyle][x + xOffset] = {}
              }

              // Prevent going out of bounds
              if (selectedPoints.length == 0) {
                if (x == 0 && direction == 'left') { return }
                else if (x == (gridCols - 1) && direction == 'right') { return }
                else if (y == 0 && direction == 'up') { return }
                else if (y == (gridRows - 1) && direction == 'down') { return }
              } else {
                // Also prevent moving a portion of the map into existing lines
                // TODO: Could improve this by only enforcing this if there's something at that boundary
                if (direction == 'right' && (sXYs[2] + 1 == x) && (sXYs[1] <= y && sXYs[3] >= y)) {
                  return
                } else if (direction == 'left' && (sXYs[0] - 1 == x) && (sXYs[1] <= y && sXYs[3] >= y)) {
                  return
                } else if (direction == 'down' && (sXYs[3] + 1 == y) && (sXYs[0] <= x && sXYs[2] >= x)) {
                  return
                } else if (direction == 'up' && (sXYs[1] - 1 == y) && (sXYs[0] <= x && sXYs[2] >= x)) {
                  return
                }
              }

              if (outsideSelection || !isWithinSelectedPoints(x, y)) {
                if (!newPointsByColor[color][lineWidthStyle][x]) {
                  newPointsByColor[color][lineWidthStyle][x] = {}
                }
                newPointsByColor[color][lineWidthStyle][x][y] = 1
                // "continue" would be more obvious but then the stations don't get set;
                //  but without this, everything doubles when drawn
                skipDrawing = true
              }

              // If x,y is within the boundaries
              if ((0 <= x && x < gridCols && 0 <= y && y < gridCols)) {
                // If the next square is within the boundaries
                if (0 <= x + xOffset && x + xOffset < gridCols && 0 <= y + yOffset && y + yOffset < gridCols) {
                  if (activeMap['stations'] && activeMap['stations'][x] && activeMap['stations'][x][y]) {
                    // drawback of v2 is needing to do stations and lines separately
                    if (outsideSelection || !isWithinSelectedPoints(x, y)) {
                      if (!newStations[x]) { newStations[x] = {} }
                      newStations[x][y] = activeMap['stations'][x][y]
                    } else {
                      if (!newStations[x + xOffset]) { newStations[x + xOffset] = {} }
                      newStations[x + xOffset][y + yOffset] = activeMap['stations'][x][y]
                    }
                  } // if stations
                  if (!skipDrawing) {
                    newPointsByColor[color][lineWidthStyle][x + xOffset][y + yOffset] = activeMap['points_by_color'][color][lineWidthStyle][x][y]
                  }
                } // next within boundaries
              } // x,y within boundaries
            } // for y
          } // for x
        } // lineWidthStyle
      } // color
      if (selectedPoints.length > 0) {
        updateSelectionUponMove(xOffset, yOffset)
      }
      activeMap['points_by_color'] = newPointsByColor
      activeMap['stations'] = newStations
    } else if (mapDataVersion == 2) {
      var newPointsByColor = {}
      var newStations = {}
      for (var color in activeMap['points_by_color']) {
        newPointsByColor[color] = {'xys': {}}
        for (var x in activeMap['points_by_color'][color]['xys']) {
          for (var y in activeMap['points_by_color'][color]['xys'][x]) {
            x = parseInt(x);
            y = parseInt(y);
            if (!Number.isInteger(x) || !Number.isInteger(y)) {
              continue;
            }

            if (!newPointsByColor[color]['xys'][x + xOffset]) {
                newPointsByColor[color]['xys'][x + xOffset] = {}
            }

            // Prevent going out of bounds
            if (x == 0 && direction == 'left') { return }
            else if (x == (gridCols - 1) && direction == 'right') { return }
            else if (y == 0 && direction == 'up') { return }
            else if (y == (gridRows - 1) && direction == 'down') { return }

            // If x,y is within the boundaries
            if ((0 <= x && x < gridCols && 0 <= y && y < gridCols)) {
              // If the next square is within the boundaries
              if (0 <= x + xOffset && x + xOffset < gridCols && 0 <= y + yOffset && y + yOffset < gridCols) {
                newPointsByColor[color]['xys'][x + xOffset][y + yOffset] = activeMap['points_by_color'][color]['xys'][x][y]
                if (activeMap['stations'] && activeMap['stations'][x] && activeMap['stations'][x][y]) {
                  // v2 drawback is needing to do stations and lines separately
                  if (!newStations[x + xOffset]) { newStations[x + xOffset] = {} }
                  newStations[x + xOffset][y + yOffset] = activeMap['stations'][x][y]
                } // if stations
              } // next within boundaries
            } // x,y within boundaries
          } // for y
        } // for x
      }
      activeMap['points_by_color'] = newPointsByColor
      activeMap['stations'] = newStations
    } else if (mapDataVersion == 1) {
      newMapObject = {}
      for (var x in activeMap) {
        for (var y in activeMap[x]) {
          x = parseInt(x);
          y = parseInt(y);
          if (!Number.isInteger(x) || !Number.isInteger(y)) {
            continue;
          }

          if (!newMapObject[x + xOffset]) {
              newMapObject[x + xOffset] = {}
          }

          // If x,y is within the boundaries
          if ((0 <= x && x < gridCols && 0 <= y && y < gridCols)) {
            // If the next square is within the boundaries
            if (0 <= x + xOffset && x + xOffset < gridCols && 0 <= y + yOffset && y + yOffset < gridCols) {
              newMapObject[x + xOffset][y + yOffset] = activeMap[x][y];
            } // next within boundaries
          } // x,y within boundaries
        } // for y
      } // for x
      newMapObject["global"] = activeMap["global"];

      activeMap = newMapObject;
    } // mapDataVersion check

    drawCanvas(activeMap);
    autoSave(activeMap)

    // This is useful because I could call this in a while loop,
    //  and when it returns for being out of bounds I can stop,
    //  and then could offer to stretch if now possible.
    // If I do that, I should defer autoSave until it's over, and only do it once.
    return true
} // moveMap(direction)

function getCornersOfSelection(points) {
  if (points.length == 0) {
    return []
  }
  var allX = []
  var allY = []
  for (var xy of points) {
    allX.push(xy[0])
    allY.push(xy[1])
  }
  return [Math.min(...allX), Math.min(...allY), Math.max(...allX), Math.max(...allY)]
} // getCornersOfSelection

function updateSelectionUponMove(xOffset, yOffset) {
  // After moving the map, the selectedPoints needs to also move
  var newSelectedPoints = structuredClone(selectedPoints)
  var x1 = MAX_MAP_SIZE, y1 = MAX_MAP_SIZE
  var x2 = 0, y2 = 0
  for (var coords in newSelectedPoints) {
    newSelectedPoints[coords][0] += xOffset || 0
    newSelectedPoints[coords][1] += yOffset || 0
  }
  selectedPoints = newSelectedPoints
  clearMarchingAnts()
  drawSelectionBox(...getCornersOfSelection(newSelectedPoints))
} // updateSelectionUponMove(xOffset, yOffset)

function disableRightClick(event) {
  // Sometimes when creating a map it's too easy to accidentally right click and it's annoying
  event.preventDefault();
}

function enableRightClick() {
  document.getElementById('grid-canvas').removeEventListener('contextmenu', disableRightClick);
  document.getElementById('hover-canvas').removeEventListener('contextmenu', disableRightClick);
  document.getElementById('ruler-canvas').removeEventListener('contextmenu', disableRightClick);
} // enableRightClick()

function getCanvasXY(pageX, pageY) {
  // Get an x, y coordinate from the canvas

  var container = $('#canvas-container')
  var width = container.width();
  var height = container.height();

  var xOffset = parseInt($('#main-container').css('padding-left'))
  var yOffset = parseInt($('#main-container').css('margin-top')) + parseInt($('#mobile-header').height())

  pageX = parseInt(pageX) - xOffset
  pageY = parseInt(pageY) - yOffset

  var x = Math.round(pageX / width * gridCols)
  var y = Math.round(pageY / height * gridRows)

  if (x < 0) {
    x = 0
  } else if (x >= gridCols) {
    x = gridCols - 1
  }

  if (y < 0) {
    y = 0
  } else if (y >= gridRows) {
    y = gridRows - 1
  }

  return [x, y]
} // getCanvasXY(pageX, pageY)

function ffSpan(color, initialColor, different) {
  // Helper function to help determine the boundaries for floodFill,
  //  because in JS, ['0896d7', '1-solid'] is not equal to ['0896d7', '1-solid']
  if (different) {
    if (color && initialColor && (color[0] != initialColor[0] || color[1] != initialColor[1])) {
      return true
    } else if (color && !initialColor) {
      return true
    } else if (!color && initialColor) {
      return true
    }
    return false
  }

  if (color === undefined && initialColor === undefined) {
    return true
  }
  if (color && initialColor && color[0] == initialColor[0] && color[1] == initialColor[1]) {
    return true
  }
  return false
} // ffSpan(color, initialColor, different)

function floodFill(x, y, initialColor, replacementColor, hoverIndicator) {
  // Note: The largest performance bottleneck is actually in
  //  drawing all the points when dealing with large areas
  // N2H: Right now, this doesn't floodFill along diagonals,
  //  but I also don't want it to bleed beyond the diagonals

  // Prevent infinite loops, but allow replacing the same color if the style is different
  if (mapDataVersion >= 3 && initialColor && initialColor[0] == replacementColor && initialColor[1] == activeLineWidthStyle) {
    return
  } else if (initialColor == replacementColor && mapDataVersion < 3) {
    return
  }

  if (!x || !y)
    return

  var x1 = false
  var spanAbove = spanBelow = 0;
  var coords = [x, y]
  var ignoreCoords = {}

  if (hoverIndicator) {
    var canvas = document.getElementById('hover-canvas')
    var ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)
  }

  if (mapDataVersion <= 2) {
    // While it might be simpler to have a unified version of this function,
    //  the differences in the return values of getActiveLine() are significant enough
    //  among the versions, and this avoids an infinite loop when flood filling over a black line (000000) in v2
    // CONSIDER: Revisit a unified version; might be able to special-case the 000000 problem
    while (coords.length > 0)
    {
      y = coords.pop()
      x = coords.pop()
      x1 = x;
      while(x1 >= 0 && getActiveLine(x1, y, activeMap, mapDataVersion >= 3) == initialColor)
        x1--;
      x1++;
      spanAbove = spanBelow = 0;
      while(x1 < gridCols && getActiveLine(x1, y, activeMap, mapDataVersion >= 3) == initialColor)
      {
        if (hoverIndicator) {
          if (ignoreCoords && ignoreCoords[x1] && ignoreCoords[x1][y])
            break
          if (!ignoreCoords.hasOwnProperty(x1))
            ignoreCoords[x1] = {}
          drawHoverIndicator(x1, y, replacementColor, 0.5)
          ignoreCoords[x1][y] = true
        } else {
          updateMapObject(x1, y, "line", replacementColor);
        }
        if(!spanAbove && y > 0 && getActiveLine(x1, y-1, activeMap, mapDataVersion >= 3) == initialColor)
        {
          coords.push(x1, y - 1);
          spanAbove = 1;
        }
        else if(spanAbove && y > 0 && getActiveLine(x1, y-1, activeMap, mapDataVersion >= 3) != initialColor)
        {
          spanAbove = 0;
        }
        if(!spanBelow && y < gridRows - 1 && getActiveLine(x1, y+1, activeMap, mapDataVersion >= 3) == initialColor)
        {
          coords.push(x1, y + 1);
          spanBelow = 1;
        }
        else if(spanBelow && y < gridRows - 1 && getActiveLine(x1, y+1, activeMap, mapDataVersion >= 3) != initialColor)
        {
          spanBelow = 0;
        }
        x1++;
      } // while x1
    } // while coords
  } else {
    while (coords.length > 0)
    {
      y = coords.pop()
      x = coords.pop()
      if (!isWithinSelectedPoints(x, y)) { continue } // This handles the rows
      x1 = x;
      while(x1 >= 0 && ffSpan(getActiveLine(x1, y, activeMap, mapDataVersion >= 3), initialColor))
        x1--;
      x1++;
      spanAbove = spanBelow = 0;
      while(x1 < gridCols && ffSpan(getActiveLine(x1, y, activeMap, mapDataVersion >= 3), initialColor))
      {
        if (hoverIndicator) {
          if (ignoreCoords && ignoreCoords[x1] && ignoreCoords[x1][y])
            break
          if (!ignoreCoords.hasOwnProperty(x1))
            ignoreCoords[x1] = {}
          if (isWithinSelectedPoints(x1, y)) {
            drawHoverIndicator(x1, y, replacementColor, 0.5)
            ignoreCoords[x1][y] = true
          }
        } else {
          if (isWithinSelectedPoints(x1, y)) {
            updateMapObject(x1, y, "line", replacementColor);
          }
        }
        if(!spanAbove && y > 0 && ffSpan(getActiveLine(x1, y-1, activeMap, mapDataVersion >= 3), initialColor) && isWithinSelectedPoints(x1, y-1))
        {
          coords.push(x1, y - 1);
          spanAbove = 1;
        }
        else if(spanAbove && y > 0 && ffSpan(getActiveLine(x1, y-1, activeMap, mapDataVersion >= 3), initialColor, true))
        {
          spanAbove = 0;
        }
        if(!spanBelow && y < gridRows - 1 && ffSpan(getActiveLine(x1, y+1, activeMap, mapDataVersion >= 3), initialColor) && isWithinSelectedPoints(x1, y+1))
        {
          coords.push(x1, y + 1);
          spanBelow = 1;
        }
        else if(spanBelow && y < gridRows - 1 && ffSpan(getActiveLine(x1, y+1, activeMap, mapDataVersion >= 3), initialColor, true))
        {
          spanBelow = 0;
        }
        x1++;
      } // while x1
    } // while coords
  } // mapDataVersion check
} // floodFill() (scanline implementation)

function combineCanvases() {
  // Combine all the separate canvases onto the main canvas so you can save the image
  drawCanvas(activeMap);
  var canvas = document.getElementById('metro-map-canvas');
  var canvasStations = document.getElementById('metro-map-stations-canvas');
  // Layer the stations on top of the canvas
  var ctx = canvas.getContext('2d', {alpha: false});
  ctx.drawImage(canvasStations, 0, 0);
  var ctxStations = canvasStations.getContext('2d', {alpha: true});
  ctxStations.clearRect(0, 0, canvasStations.width, canvasStations.height);
  return canvas
} // combineCanvases()

function downloadImage(canvas, showImg) {
  // Generates the necessary image data based on browser capability
  //  and applies it to the hidden link
  var pngFilename = 'metromapmaker.png' // Maybe: it might be nice to name this as the user-given map name, or the known/canonical map name when available (though it will need to be sanitized)
  if (!HTMLCanvasElement.prototype.toBlob) {
    var imageData = canvas.toDataURL()
    $('#metro-map-image-download-link').attr({
      "download": pngFilename,
      "href": imageData
    })
    if (showImg) {
      $('#grid-canvas').hide();
      $('#hover-canvas').hide();
      $('#ruler-canvas').hide();
      $('#metro-map-canvas').hide();
      $('#metro-map-stations-canvas').hide();
      $('#metro-map-image').attr('src', imageData)
      $('#metro-map-image').show()
    } else {
      document.getElementById('metro-map-image-download-link').click()
      drawCanvas(activeMap) // repaint the canvas, because otherwise the stations are drawn twice
    }
  } else {
    if (pngUrl) {
      // Revoke any previously-created blobs
      URL.revokeObjectURL(pngUrl)
    }
    canvas.toBlob(function(blob) {
      pngUrl = URL.createObjectURL(blob)
      $('#metro-map-image-download-link').attr({
        "download": pngFilename,
        "href": pngUrl
      })
      if (showImg) {
        $('#grid-canvas').hide();
        $('#hover-canvas').hide();
        $('#ruler-canvas').hide();
        $('#metro-map-canvas').hide();
        $('#metro-map-stations-canvas').hide();
        $('#metro-map-image').attr('src', pngUrl)
        $('#metro-map-image').show()
      } else {
        document.getElementById('metro-map-image-download-link').click()
        drawCanvas(activeMap) // repaint the canvas, because otherwise the stations are drawn twice
      } // else
    }) // canvas.toBlob()
  } // else (.toBlob available)
} // downloadImage()

function resetResizeButtons(size) {
  $('.resize-grid').each(function() {
    if ($(this).text().indexOf('Current') > -1) {
      var resizeButtonSize = $(this).attr('id').split('-').slice(2);
      var resizeButtonLabel = resizeButtonSize + 'x' + resizeButtonSize;
      $(this).text(resizeButtonLabel);
    }
  })
  $('#tool-resize-' + size).text('Current size (' + size + 'x' + size + ')');
  if (isMapStretchable(size)) {
    $('#tool-resize-stretch').show()
    $('#tool-resize-stretch').text('Stretch map to ' + size * 2 + 'x' + size * 2)
  } else {
    $('#tool-resize-stretch').hide()
  }
} // function resetResizeButtons()

function resetStyleButtons() {
  $('.map-style-line.active-mapstyle').removeClass('active')
  $('.map-style-line.active-mapstyle').removeClass('active-mapstyle')
  $('.map-style-station.active-mapstyle').removeClass('active')
  $('.map-style-station.active-mapstyle').removeClass('active-mapstyle')
  if (activeMap && activeMap['global'] && activeMap['global']['style']) {
    var width = activeMap['global']['style']['mapLineWidth']
    var stationStyle = activeMap['global']['style']['mapStationStyle']
    if (width) {
      $('#tool-map-style-line-' + parseInt(width * 1000)).addClass('active-mapstyle')
    }
    if (stationStyle) {
      $('#tool-map-style-station-' + stationStyle).addClass('active-mapstyle')
      $('#reset-all-station-styles').text('Set ALL stations to ' + $('#tool-map-style-station-' + stationStyle).text())
    }
  }
} // resetStyleButtons()

function throttle(callback, interval) {
  let enableCall = true;

  return function(...args) {
    if (!enableCall) return;

    enableCall = false;
    callback.apply(this, args);
    setTimeout(() => enableCall = true, interval);
  }
} // throttle()

function resetTooltipOrientation() {
  tooltipOrientation = ''
  if (window.innerWidth <= 768)
    tooltipOrientation = 'top'
  else if (!$('#snap-controls-right').is(':hidden'))
    tooltipOrientation = 'right'
  else
    tooltipOrientation = 'left'
  $('.has-tooltip').each(function() {
    if ($(this).data('bs.tooltip'))
      $(this).data('bs.tooltip').options.placement = tooltipOrientation
  })
} // resetTooltipOrientation()

function resetRailLineTooltips() {
  // Re-set rail line keyboard shortcut tooltips
  var allLines = $('.rail-line');
  var keyboardShortcut = ''
  for (var a=0; a<allLines.length; a++) {
    var line = $('.rail-line')[a].id.slice(10, 16)
    if (a < 10) {
      keyboardShortcut = 'Keyboard shortcut: ' + numberKeys[a].replace('Digit', '')
    } else if (a < 20) {
      keyboardShortcut = 'Keyboard shortcut: Shift + ' + numberKeys[a].replace('Digit', '')
    } else if (a < 30) {
      keyboardShortcut = 'Keyboard shortcut: Alt + ' + numberKeys[a].replace('Digit', '')
    } else {
      keyboardShortcut = '' // remove old tooltips
    }
    $('#rail-line-' + line).attr('title', keyboardShortcut).tooltip('fixTitle')
  } // for a in allLines
  resetTooltipOrientation()
} // resetRailLineTooltips

function showGrid() {
  $('canvas#grid-canvas').css("opacity", 1);
}

function hideGrid() {
  $('canvas#grid-canvas').css("opacity", 0);
}

function setFloodFillUI() {
  // Show appropriate eraser warnings when flood fill is set
  if ($('#tool-flood-fill').prop('checked')) {

    $('#tool-line-icon-pencil').hide()
    $('#tool-line-caption-draw').hide()

    $('#tool-line-icon-paint-bucket').show()
    $('#tool-eraser-icon-paint-bucket').show()

    $('#tool-eraser-icon-eraser').hide()
    $('#tool-eraser-caption-eraser').hide()

    if (!menuIsCollapsed) {
      $('#tool-line-caption-fill').show()
      $('#tool-eraser-caption-fill').show()
    }

    if ((activeTool == 'line' && activeToolOption) || activeTool == 'eraser') {
      if (activeTool == 'line' && activeToolOption)
        indicatorColor = activeToolOption
      else
        indicatorColor = '#ffffff'
      floodFill(hoverX, hoverY, getActiveLine(hoverX, hoverY, activeMap, (mapDataVersion >= 3)), indicatorColor, true)
    }
  } else {
    $('#tool-line-icon-pencil').show()
    $('#tool-eraser-icon-eraser').show()

    $('#tool-line-icon-paint-bucket').hide()
    $('#tool-line-caption-fill').hide()

    if (!menuIsCollapsed) {
      $('#tool-line-caption-draw').show()
      $('#tool-eraser-caption-eraser').show()
    }

    $('#tool-eraser-icon-paint-bucket').hide()
    $('#tool-eraser-caption-fill').hide()

    $('#tool-eraser-options').hide()
    var canvas = document.getElementById('hover-canvas')
    var ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    if ((activeTool == 'line' && activeToolOption) || activeTool == 'eraser') {
      if (activeTool == 'line' && activeToolOption)
        indicatorColor = activeToolOption
      else
        indicatorColor = '#ffffff'
      drawHoverIndicator(hoverX, hoverY, indicatorColor)
    }
  }

} // setFloodFillUI()

function setURLAfterSave(urlhash) {
  // Note: Easy to do but the more I think about this,
  // I think it'll be confusing behavior likely to lead to frustration,
  // and less important when people can find their own maps in the calendar.
  var currentUrl = window.location.href.split('=')[0]
  // HEADS UP: If you bring this back,
  // it will need to handle /map/<urlhash> being equivalent to ?map=<urlhash>
  // if (currentUrl.indexOf('?map') > -1) {
  //   window.history.pushState(null, "", currentUrl + '=' + urlhash)
  // } else {
  //   window.history.pushState(null, "", currentUrl + '?map=' + urlhash)
  // }
}

$(document).ready(function() {

  document.getElementById('canvas-container').addEventListener('click', bindGridSquareEvents, false);
  document.getElementById('canvas-container').addEventListener('mousedown', bindGridSquareMousedown, false);
  // document.getElementById('canvas-container').addEventListener('mousemove', throttle(bindGridSquareMouseover, 1), false);
  // Trying without throttle to see if we get a smoother draw
  document.getElementById('canvas-container').addEventListener('mousemove', bindGridSquareMouseover, false);
  document.getElementById('canvas-container').addEventListener('mouseup', bindGridSquareMouseup, false);

  // Better support for mobile
  // TODO: This works okay, but but has a few big problems:
  // 1. The canvas frequently crashes on iOS Safari and iOS Chrome,
  //  rendering as a black field. Perhaps clearing the canvases in a different way would help.
  // 2. Canvas performance is extremely poor. Possibly dropping bindGridSquareMouseover on touchmove could help, but this is surely linked with the canvas crashes.
  // 3. Would need to add a better way of scrolling (perhaps use two fingers to scroll),
  //  so that you don't draw/erase as you're scrolling
  // document.getElementById('canvas-container').addEventListener('touchstart', function(e) {
  //   console.log(`DEBUG: touchstart at ${e.pageX},${e.pageY}`)
  //   bindGridSquareEvents(e)
  // }, false);
  // document.getElementById('canvas-container').addEventListener('touchmove', function(e) {
  //   console.log(`DEBUG: touchmove at ${e.pageX},${e.pageY}`)
  //   if (!$('#tool-flood-fill').prop('checked')) {
  //     var xy = getCanvasXY(event.pageX, event.pageY)
  //       if (activeTool == 'line' && activeToolOption) {
  //       makeLine(xy[0], xy[1])
  //     } else if (activeTool == 'eraser') {
  //       erase(xy[0], xy[1])
  //     }
  //   }
  //   bindGridSquareMouseover(e)
  // }, false);
  // document.getElementById('canvas-container').addEventListener('touchend', function(e) {
  //   console.log(`DEBUG: touchend at ${e.pageX},${e.pageY}`)
  //   bindGridSquareMouseup(e)
  // }, false);
  // document.getElementById('canvas-container').addEventListener('touchcancel', function(e) {
  //   console.log(`DEBUG: touchcancel at ${e.pageX},${e.pageY}`)
  //   bindGridSquareMouseup(e)
  // }, false);
  // -----------------------------------------------------------------------------------

  window.addEventListener('resize', unfreezeMapControls);
  window.addEventListener('scroll', function() {
    $('.tooltip').hide()
  })

  // Bind to the mousedown and mouseup events so we can implement dragging easily
  mouseIsDown = false;

  // Disable right-click on the grid/hover canvases (but not on the map canvas/image)
  document.getElementById('grid-canvas').addEventListener('contextmenu', disableRightClick);
  document.getElementById('hover-canvas').addEventListener('contextmenu', disableRightClick);
  document.getElementById('ruler-canvas').addEventListener('contextmenu', disableRightClick);

  // Enable the tooltips
  $(function () {
    $('[data-toggle="tooltip"]').tooltip({"container": "body"});
    // If on mobile, set initial tooltip direction
    if (window.innerWidth <= 768) {
      $('.has-tooltip').each(function() {
        if ($(this).data('bs.tooltip'))
          $(this).data('bs.tooltip').options.placement = 'top'
      })
    }
  })

  document.addEventListener("keydown", function(event) {
    // Don't use keyboard shortcuts if any text input has focus
    if (document.activeElement && document.activeElement.type == 'text') {
      if (event.key == 'Enter') { // Enter
        // If focused on the rail line name, save the line
        if (document.activeElement.id == 'new-rail-line-name')
          $('#create-new-rail-line').click()
        else if (document.activeElement.id == 'change-line-name')
          $('#save-rail-line-edits').click()
        // Unset the focus from the text box when hitting Enter
        document.activeElement.blur()
      }
      return
    }

    // Define keyboard shortcuts here
    var possibleRailLines = $('.rail-line')
    var railKey = false

    if ((event.key.toLowerCase() == 'c') && (!event.metaKey && !event.altKey && !event.ctrlKey)) { // C
      if (menuIsCollapsed) {
        $('#controls-expand-menu').trigger('click')
      } else {
        $('#controls-collapse-menu').trigger('click')
      }
    }
    else if (event.key.toLowerCase() == 'd') { // D
      $('#tool-line').trigger('click')
    }
    else if (event.key.toLowerCase() == 'e') { // E
      $('#tool-eraser').trigger('click')
    }
    else if (event.key.toLowerCase() == 'f') { // F
      if ($('#tool-flood-fill').prop('checked')) {
        $('#tool-flood-fill').prop('checked', false)
      } else {
        $('#tool-flood-fill').prop('checked', true)
        if (activeTool == 'eraser') {
          setActiveTool('eraser')
        } else if (activeToolOption) {
          // On the assumption that activeToolOption is only for line color,
          //  which has been true so far
          setActiveTool('line')
        }
      }
      setFloodFillUI()
    }
    else if (event.key.toLowerCase() == 'g') { // G
      if ($('#straight-line-assist').prop('checked')) {
        $('#straight-line-assist').prop('checked', false)
        var canvas = document.getElementById('hover-canvas')
        var ctx = canvas.getContext('2d')
        ctx.clearRect(0, 0, canvas.width, canvas.height)
      } else {
        $('#straight-line-assist').prop('checked', true)
        if (mouseIsDown && (activeTool == 'line' || activeTool == 'eraser')) {
          for (var x=0; x<gridRows; x++) {
            for (var y=0; y<gridCols; y++) {
              if (x == clickX || y == clickY || Math.abs(x - clickX) == Math.abs(y - clickY)) {
                drawHoverIndicator(x, y, '#2E71CC')
              } // if it's a straight line from the origin
            } // for y
          } // for x
        }
      } // #straight-line-assist checked?
    }
    else if (event.key.toLowerCase() == 'h') { // H
      $('#tool-grid').trigger('click')
    }
    else if (event.key.toLowerCase() == 'k' && (!event.metaKey && !event.altKey && !event.ctrlKey)) {
      $('#tool-look').trigger('click')
    }
    else if (event.key.toLowerCase() == 'l')  { // L
      $('#tool-label').trigger('click')
    }
    else if (event.key.toLowerCase() == 'm')  { // M
      if (activeTool == 'station' && $('#tool-station-options').is(':visible')) {
        $('#move-station').trigger('click')
      } else {
        setMoveStationAbility(true) // disable it
      }
      if (activeTool != 'station' && selectedPoints.length > 0) {
        $('#tool-move-selection').trigger('click')
      }
    }
    else if (event.key.toLowerCase() == 'o' && (!event.metaKey && !event.altKey && !event.ctrlKey)) { // O, except for Open
      if (activeTool == 'station' && $('#tool-station-options').is(':visible')) {
        cycleSelectMenu(document.getElementById('station-name-orientation'), event.shiftKey ? -1 : 1)
      }
    }
    else if (event.key.toLowerCase() == 'p' && (!event.metaKey && !event.altKey && !event.ctrlKey)) { // P, except for Print
      $('#tool-eyedropper').trigger('click')
    }
    else if (event.key.toLowerCase() == 'q' && (!event.metaKey && !event.altKey && !event.ctrlKey)) { // Q, except for quit
      if (mapDataVersion >= 3) {
        cycleLineStyle(event.shiftKey ? -1 : 1)
      }
    }
    else if (event.key.toLowerCase() == 'r' && (!event.metaKey && !event.altKey && !event.ctrlKey)) { // R, except for Refresh
      $('#tool-ruler').trigger('click')
    }
    else if (event.key.toLowerCase() == 's') { // S
      $('#tool-station').trigger('click')
    }
    else if (event.key.toLowerCase() == 't') {
      $('#tool-select').trigger('click')
      // If you press T, to me, you want to select again,
      //  even if you're clearing the selection.
      // If you press Escape, you're just clearing the selection,
      //  and will return to your previous tool
      setActiveTool('select', true)
    }
    else if (event.key.toLowerCase() == 'w' && (!event.metaKey && !event.altKey && !event.ctrlKey)) { // W, except for close window
      if (mapDataVersion >= 3) {
        cycleLineWidth(event.shiftKey ? -1 : 1)
      }
    }
    else if ((event.key.toLowerCase() == 'x') && (!event.metaKey && !event.ctrlKey)) { // X
      if (activeTool == 'station' && $('#tool-station-options').is(':visible')) {
        $('#station-transfer').trigger('click')
      }
    }
    else if (event.key.toLowerCase() == 'y' && (event.metaKey || event.ctrlKey)) { // Ctrl + Y
      event.preventDefault() // Don't open the History menu
      redo();
    }
    else if ((event.key.toLowerCase() == 'y') && (!event.metaKey && !event.ctrlKey)) { // Y
      if (activeTool == 'station' && $('#tool-station-options').is(':visible')) {
        cycleSelectMenu(document.getElementById('station-style'), event.shiftKey ? -1 : 1)
      }
      else if (!menuIsCollapsed && mapDataVersion > 1) {
        $('#tool-map-style').trigger('click')
      }
    }
    else if (event.key.toLowerCase() == 'z' && (event.metaKey || event.ctrlKey)) { // Ctrl + Z
      event.preventDefault() // On Safari, don't open a recently-closed window
      undo();
    }
    else if (event.key == 'ArrowLeft' && (!event.metaKey && !event.altKey && !event.ctrlKey)) { // left arrow, except for "go back"
      event.preventDefault();
      if (activeTool == 'station' && $('#tool-station-options').is(':visible')) {
        arrowKeys.add('left')
      }
      else {
        moveMap('left')
      }
    }
    else if (event.key == 'ArrowUp') { // up arrow
      event.preventDefault();
      if (activeTool == 'station' && $('#tool-station-options').is(':visible')) {
        arrowKeys.add('up')
      } else {
        moveMap('up')
      }
    }
    else if (event.key == 'ArrowRight' && (!event.metaKey && !event.altKey && !event.ctrlKey)) { // right arrow, except for "go forward"
      event.preventDefault();
      if (activeTool == 'station' && $('#tool-station-options').is(':visible')) {
        arrowKeys.add('right')
      } else {
        moveMap('right')
      }
    }
    else if (event.key == 'ArrowDown') { // down arrow
      event.preventDefault();
      if (activeTool == 'station' && $('#tool-station-options').is(':visible')) {
        arrowKeys.add('down')
      } else {
        moveMap('down')
      }
    }
    else if (event.key == '-' || event.key == '_') { // minus
      if ((event.metaKey || event.ctrlKey) && (event.key == '-' || event.key == '_')) {
        // Prevent the browser built-in Zoom out, because it's not actually helpful
        event.preventDefault()
      }
      $('#tool-zoom-out').trigger('click')
    }
    else if (event.key == '=' || event.key == '+') { // plus / equal sign
      if ((event.metaKey || event.ctrlKey) && (event.key == '=' || event.key == '+')) {
        // Prevent the browser built-in Zoom in, because it's not actually helpful
        event.preventDefault()
      }
      $('#tool-zoom-in').trigger('click')
    }
    else if (event.code == 'BracketLeft') { // [
      $('#snap-controls-left').trigger('click')
    }
    else if (event.code == 'BracketRight') { // ]
      $('#snap-controls-right').trigger('click')
    }
    // 0-9, except when switching tabs (Control)
    // Check shift key first, for 11-20; alt key for 21-30; then with no modifying key for 1-10
    else if (!event.metaKey && !event.ctrlKey && event.shiftKey && numberKeys.indexOf(event.code) >= 0) {
      railKey = numberKeys.indexOf(event.code) + 10
    }
    else if (!event.metaKey && !event.ctrlKey && event.altKey && numberKeys.indexOf(event.code) >= 0) {
      railKey = numberKeys.indexOf(event.code) + 20
    }
    else if (!event.metaKey && !event.ctrlKey && numberKeys.indexOf(event.code) >= 0) {
      // Draw rail colors in order of appearance, 1-10 (0 is 10)
      railKey = numberKeys.indexOf(event.code)
    }
    else if (event.key == 'Escape' && selectedPoints.length > 0) {
      // De-select current selection, cancel any move in progress
      setActiveTool(lastToolUsed, true)
      selectedPoints = []
      clearMarchingAnts()
    }
    else if ((event.key == 'Delete' || event.key == 'Backspace') && selectedPoints.length > 0) {
      setActiveTool('eraser')
      for (var xy of selectedPoints) {
        erase(xy[0], xy[1], true) // defer save and drawCanvas, but we have to do it manually
      }
      autoSave(activeMap)
      drawCanvas(activeMap)
      setActiveTool(lastToolUsed, true)
    }

    // ----- Note: This is a separate conditional from the event.code keydowns
    if (railKey !== false && possibleRailLines[railKey]) {
      possibleRailLines[railKey].click()
    }

    if (arrowKeys.size > 0 && activeTool == 'station' && $('#tool-station-options').is(':visible')) {
      moveStation(arrowKeys)
    }
  }); // document.addEventListener("keydown")

  document.addEventListener("keyup", function(event) {
    if (arrowKeys.size > 0) {
      arrowKeys = new Set()
    }
  }); // keyup

  setActiveTool('look')

  $('#toolbox button:not(.rail-line)').on('click', function() {
    $('.active').removeClass('active')
    $(this).addClass('active')
    if (activeTool == 'line') {
      $('#tool-line').addClass('active')
    } else if (activeTool == 'eraser') {
      $('#tool-eraser').addClass('active')
    } else if (activeTool == 'station') {
      $('#tool-station').addClass('active')
    }
    if (!rulerOn && $(this).attr('id') == 'tool-ruler') {
      $(this).removeClass('active')
    }
  })
  $('#toolbox button.rail-line').on('click', function() {
    $('.active').removeClass('active')
    $('#tool-line').addClass('active')
  })

  // Toolbox
  $('#tool-line').on('click', function() {
    $('.active').removeClass('active')
    $('#tool-line').addClass('active')
    if ($(this).hasClass('draw-rail-line') && activeToolOption) {
      setActiveTool('line')
      $(this).css({"background-color": activeToolOption})
    } else if (activeTool == 'eraser' && activeToolOption) {
      setActiveTool('line')
    } else if (activeTool == 'eraser') {
      setActiveTool('look')
    }
    // Expand Rail line options
    if ($('#tool-line-options').is(':visible')) {
      $('#tool-line-options').hide();
      $('#tool-new-line-options').hide();
      if (!$('#tool-station').hasClass('width-100')) {
        $(this).removeClass('width-100')
      }
      // Also reset the + Add New Color button
      $('#rail-line-new span').text('Add New Color')
      $('#tool-new-line-options').hide()
    } else {
      $('#tool-line-options').show();
      $(this).addClass('width-100')
    }
    $('.tooltip').hide();
  }); // #tool-line.click() (Show rail lines you can paint)
  $('#tool-flood-fill').change(function() {
    setFloodFillUI()
  }) // #tool-flood-fill.change()
  $('#rail-line-delete').click(function() {
    // Only delete lines that aren't in use
    var allLines = $('.rail-line');
    var linesToDelete = [];
    var metroMap = Object.assign({}, activeMap) // make a copy so we can check to see which lines exist
    // If the line tool is in use, unset it so we don't get a stale color
    if (activeTool == 'line') {
      setActiveTool('look')
      $('#tool-line').attr('style', '')
      $('#tool-line').removeClass('active')
    }
    if (mapDataVersion == 2 || mapDataVersion == 3) {
      for (var color of allLines) {
        color = color.id.slice(10, 16)
        if (!colorInUse(color)) {
          linesToDelete.push($('#rail-line-' + color))
          delete activeMap['global']['lines'][color]
        }
      }
    } else if (mapDataVersion == 1) {
      delete metroMap["global"] // This is okay, it's a copy of activeMap, and we need to avoid matching what's in ['lines'] when we're doing an indexOf
      metroMap = JSON.stringify(metroMap)
      for (var a=0; a<allLines.length; a++) {
        if ($('.rail-line')[a].id != 'rail-line-new') {
          // Is this line in use at all?
          if (metroMap.indexOf('"line":"' + $('.rail-line')[a].id.slice(10, 16) + '"') == -1) {
            linesToDelete.push($('#' + $('.rail-line')[a].id));
            delete activeMap["global"]["lines"][$('.rail-line')[a].id.split("-").slice(2,3)]
          }
        }
      }
    }
    if (linesToDelete.length > 0) {
      autoSave(activeMap)
      for (var d=0; d<linesToDelete.length; d++) {
        linesToDelete[d].remove();
      }
      resetRailLineTooltips()
    } // if linesToDelete.length > 0
    drawCanvas() // This also does a full reset of the color map
  }); // #rail-line-delete.click() (Delete unused lines)
  $('#tool-station').click(function() {
    setActiveTool('station')
    $('.active').removeClass('active')
    $('#tool-station').addClass('active')
    if ($('#tool-station-options').is(':visible')) {
      $('#tool-station-options').hide();
      setMoveStationAbility(true) // turn off "Move Station"
      $(this).removeClass('width-100')
    }
    $('.tooltip').hide();
  }); // #tool-station.click()
  $('#tool-label').on('click', function() {
    setActiveTool('label')
    $('.active').removeClass('active')
    $(this).addClass('active')
    if ($('#tool-label-options').is(':visible')) {
      $('#tool-label-options').hide()
      $(this).removeClass('width-100')
    }
  })
  $('#tool-eraser').on('click', function() {
    setActiveTool('eraser')
    $('.active').removeClass('active')
    $('#tool-eraser').addClass('active')
    $('#tool-station-options').hide();
    setMoveStationAbility(true) // turn off "Move Station"
    $('.tooltip').hide();
    $('#tool-line').attr('style', '')
    if (!$('#tool-line-options').is(':visible')) {
      $('#tool-line').removeClass('width-100')
    }
    $('#tool-station').attr('style', '')
    if (!$('#tool-station-options').is(':visible')) {
      $('#tool-station').removeClass('width-100')
    }
    setFloodFillUI()
  }); // #tool-eraser.click()
  $('#tool-grid').click(function() {
    cycleGridStep()
    $('.tooltip').hide()
  }); // #tool-grid.click() (Toggle grid visibility)
  $('#tool-zoom-in').click(function() {
      resizeCanvas('in')
  }); // #tool-zoom-in.click()
  $('#tool-zoom-out').click(function() {
    resizeCanvas('out')
  }); // #tool-zoom-out.click()
  $('#snap-controls-left').click(function() {
    $('#controls').css("left", 5)
    $('#controls').css("right", "unset")
    $('.has-tooltip').each(function() {
      if ($(this).data('bs.tooltip'))
        $(this).data('bs.tooltip').options.placement = 'right'
    })
    $(this).hide()
    $('#snap-controls-right').show()
  }); // #snap-controls-left.click()
  $('#snap-controls-right').click(function() {
    $('#controls').css("right", 5)
    $('#controls').css("left", "unset")
    $('.has-tooltip').each(function() {
      if ($(this).data('bs.tooltip'))
        $(this).data('bs.tooltip').options.placement = 'left'
    })
    $(this).hide()
    $('#snap-controls-left').show()
  }); // #snap-controls-right.click()
  $('#tool-resize-all').click(function() {
    if ($('#tool-resize-options').is(':visible')) {
      $('#tool-resize-options').hide();
      $(this).removeClass('width-100')
      $(this).removeClass('active')
    } else {
      $('#tool-resize-options').show();
      $(this).addClass('width-100')
      if (isMapStretchable()) {
        $('#tool-resize-stretch').show()
        $('#tool-resize-stretch').text('Stretch map to ' + gridRows * 2 + 'x' + gridCols * 2)
      } else {
        $('#tool-resize-stretch').hide()
      }
    }
    $('.tooltip').hide();
  }); // #tool-resize-all.click()
  $('.resize-grid').click(function() {
    var lastToolUsed = activeTool;
    setActiveTool('resize')
    size = $(this).attr('id').split('-').slice(2);
    // Indicate which size the map is now sized to, and reset any other buttons
    resetResizeButtons(size)
    if (mapDataVersion >= 2) {
        activeMap['global']['map_size'] = parseInt(size)
    }
    setMapSize(activeMap, true)
    activeTool = lastToolUsed; // Reset tool after drawing the grid to avoid undefined behavior when eraser was the last-used tool
    autoSave(activeMap)
  }); // .resize-grid.click()
  $('#tool-resize-stretch').click(function() {
    stretchMap()
    autoSave(activeMap)
  }) // #tool-resize-stretch.click()
  $('#tool-move-all').on('click', function() {
    if ($('#tool-move-options').is(':visible')) {
      $('#tool-move-options').hide();
      $(this).removeClass('active')
      $(this).removeClass('width-100')
    } else {
      $('#tool-move-options').show();
      $(this).addClass('width-100')
    }
    $('.tooltip').hide();
  }); // #tool-move-all.click()
  $('#tool-move-up').click(function() {
    moveMap("up");
  }); // #tool-move-up.click()
  $('#tool-move-down').click(function() {
    moveMap("down");
  }); // #tool-move-down.click()
  $('#tool-move-left').click(function() {
    moveMap("left");
  }); // #tool-move-left.click()
  $('#tool-move-right').click(function() {
    moveMap("right");
  }); // #tool-move-right.click()
  $('#tool-save-map').click(function() {
    setActiveTool('look')
    var savedMap = JSON.stringify(activeMap);
    autoSave(savedMap);
    var saveMapURL = '/save/';
    csrftoken = getCookie('csrftoken');
    // Disable button (and re-enable it shortly thereafter
    $('#tool-save-map').prop('disabled', 'disabled')
    $('#tool-save-map span').text('Saving ...')
    setTimeout(function() {
      // Re-enable it after 1 second no matter what,
      //  but the visual cue ("Saving ...")
      //  won't change until the map is actually saved
      $('#tool-save-map').prop('disabled', false)
    }, 1000)
    $.post( saveMapURL, {
      'metroMap': savedMap,
      'csrfmiddlewaretoken': csrftoken
    }).done(function(data) {
      if (data.replace(/\n/g, '').indexOf('No points_by_color') > -1) {
        $('#tool-save-options').html('<h5 class="bg-danger">You can\'t save an empty map.</h5>');
        $('#tool-save-options').show();
      }
      else if (data.replace(/\s/g,'').slice(0,7) == '[ERROR]') {
        $('#tool-save-options').html('<h5 class="bg-danger">Sorry, there was a problem saving your map: ' + data.slice(9) + '</h5>');
        console.log("[WARN] Problem was: " + data)
        $('#tool-save-options').show();
      }
      else {
        if (menuIsCollapsed) {
          $('#controls-expand-menu').trigger('click')
        }

        data = data.split(',');
        var urlhash = data[0].replace(/\s/g,'');
        var namingToken = data[1].replace(/\s/g,'');
        var toolSaveOptions = '<button id="hide-save-share-url" class="styling-greenline width-100">Hide sharing explanation</button><h5 style="overflow-x: hidden;" class="text-left">Map Saved! You can share your map with a friend by using this link: <a id="shareable-map-link" href="/map/' + urlhash + '" target="_blank">metromapmaker.com/map/' + urlhash + '</a></h5> <h5 class="text-left">You can then share this URL with a friend - and they can remix your map without you losing your original! <b>If you make changes to this map, click Save &amp; Share again to get a new URL.</b></h5>';
        // setURLAfterSave(urlhash)
        if (namingToken) {
          // Only show the naming form if the map could actually be renamed.
          toolSaveOptions += '<form id="name-map" class="text-left"><input type="hidden" name="urlhash" value="' + urlhash + '"><input id="naming-token" type="hidden" name="naming_token" value="' + namingToken + '"><label for="name">Where is this a map of?</label><input id="user-given-map-name" type="text" name="name"><select id="user-given-map-tags" name="tags"><option value="">What kind of map is this?</option><option value="real">This is a real metro system</option><option value="speculative">This is a real place, but a fantasy map</option><option value="unknown">This is an imaginary place</option></select></form><button id="name-this-map" class="styling-blueline width-100">Name this map</button>'
        }
        var userGivenMapName = window.sessionStorage.getItem('userGivenMapName')
        var userGivenMapTags = window.sessionStorage.getItem('userGivenMapTags')

        if (namingToken && userGivenMapName && userGivenMapTags) {
          toolSaveOptions += '<h5><a id="map-somewhere-else">Not a map of ' + userGivenMapName + '? Click here to rename</a></h5>'
        }
        $('#tool-save-options').html('<fieldset><legend>Save &amp; Share</legend>' + toolSaveOptions + '</fieldset>');

        // Pre-fill the name and tags with what we have in sessionStorage
        if (namingToken && userGivenMapName) {
          $('#user-given-map-name').val(userGivenMapName)
        }
        if (namingToken && userGivenMapTags) {
          $('#user-given-map-tags').val(userGivenMapTags)
        }

        $('#name-map').submit(function(e) {
          e.preventDefault();
        });
        $('#map-somewhere-else').click(function() {
          $('#name-map').show()
          $('#name-this-map').show()
          $(this).parent().hide()
          $('#name-this-map').removeClass();
          $('#name-this-map').addClass('styling-blueline width-100');
          $('#name-this-map').text('Name this map')
        })
        $('#name-this-map').click(function(e) {

          var formData = $('#name-map').serializeArray().reduce(function(obj, item) {
              obj[item.name] = item.value;
              return obj;
          }, {});

          // Using sessionStorage instead of localStorage means that this will only survive for the current session and will expire upon browser close
          window.sessionStorage.setItem('userGivenMapName', $('#user-given-map-name').val())
          window.sessionStorage.setItem('userGivenMapTags', $('#user-given-map-tags').val())

          csrftoken = getCookie('csrftoken');
          formData['csrfmiddlewaretoken'] = csrftoken

          $.post('/name/', formData, function() {
            $('#name-map').hide();
            $('#name-this-map').text('Thanks!')
            setTimeout(function() {
              $('#name-this-map').hide();
            }, 500);
          });
        }) // #name-this-map.click()
        if (namingToken && userGivenMapName && userGivenMapTags) {
          $('#user-given-map-name').show()
          $('#user-given-map-tags').show()
          $('#name-this-map').click()
          $('#name-this-map').hide()
        }
        $('#tool-save-options').show();

        $('#hide-save-share-url').click(function() {
          $('#tool-save-options').hide()
        })
      } // else (success)
    }).fail(function(data) {
      if (data.status == 400) {
        var message = 'Sorry, your map could not be saved. Did you flood fill the whole map? Use flood fill with the eraser to erase and try again.'
      } else if (data.status == 500) {
        var message = 'Sorry, your map could not be saved right now. This may be a bug, and the admin has been notified.'
      } else if (data.status >= 502) {
        var message = 'Sorry, your map could not be saved right now. Metro Map Maker is currently undergoing routine maintenance including bugfixes and upgrades. Please try again in a few minutes.'
      }
      $('#tool-save-options').html('<h5 class="text-left bg-warning">' + message + '</h5>');
      $('#tool-save-options').show();
    }).always(function() {
      setTimeout(function() {
        $('#tool-save-map span').text('Save & Share')
      }, 350) // A short delay looks nicer than immediate
    });
    $('.tooltip').hide();
  }); // $('#tool-save-map').click()
  $('#tool-download-image').click(function() {
    setActiveTool('look')

    // Download image on desktop, which is more robust than on mobile

    var canvas = combineCanvases()
    downloadImage(canvas)

    $('.tooltip').hide();
  }); // #tool-download-image.click()
  $('#tool-export-canvas').click(function() {
    setActiveTool('look')
    // On mobile, you need to tap and hold on the canvas to save the image
    drawCanvas(activeMap);
    $('#tool-station-options').hide();
    setMoveStationAbility(true) // turn off "Move Station"

    $('.tooltip').hide();
    if ($('#grid-canvas').is(':visible')) {
      $('#grid-canvas').hide();
      $('#hover-canvas').hide();
      $('#ruler-canvas').hide();
      $('#metro-map-canvas').hide();
      $('#metro-map-stations-canvas').hide();
      var canvas = document.getElementById('metro-map-canvas');
      var canvasStations = document.getElementById('metro-map-stations-canvas');
      // Layer the stations on top of the canvas
      var ctx = canvas.getContext('2d', {alpha: false});
      ctx.drawImage(canvasStations, 0, 0);
      var imageData = canvas.toDataURL()
      $("#metro-map-image").attr("src", imageData);
      $("#metro-map-image").show();
      $('#export-canvas-help').show();
      $('button:not(.mobile-browse)').attr('disabled', true);
      $(this).attr('disabled', false);

      $(this).attr('title', "Go back to editing your map").tooltip('fixTitle').tooltip('show');
    } else {
      $('#grid-canvas').show();
      $('#hover-canvas').show();
      $('#ruler-canvas').show();
      $('#metro-map-canvas').show();
      $('#metro-map-stations-canvas').show();
      $("#metro-map-image").hide();
      $('#export-canvas-help').hide();
      $('button').attr('disabled', false);

      $(this).attr('title', "Download your map to share with friends").tooltip('fixTitle').tooltip('show');
    }
  }); // #tool-export-canvas.click()
  $('#tool-clear-map').click(function() {
    gridRows = 80, gridCols = 80;

    activeMap = {
      "global": Object.assign({}, activeMap["global"]),
      "points_by_color": {},
      "stations": {},
    }

    activeMap['global']['map_size'] = 80

    // I wouldn't autoSave, but if I don't,
    //  and you Clear -> Undo -> Clear -> Undo
    //  then the map isn't restored on Undo as it should be
    autoSave(activeMap)

    snapCanvasToGrid()
    drawGrid()
    lastStrokeStyle = undefined;
    drawCanvas(activeMap, false, true)
    drawCanvas(activeMap, true, true)

    window.sessionStorage.removeItem('userGivenMapName');
    window.sessionStorage.removeItem('userGivenMapTags');

    $('.resize-grid').each(function() {
      var resizeButtonSize = $(this).attr('id').split('-').slice(2);
      var resizeButtonLabel = resizeButtonSize + ' x ' + resizeButtonSize;
      if (resizeButtonSize == ALLOWED_SIZES[0]) {
        resizeButtonLabel = resizeButtonLabel + ' (Current size)';
      } else {
        resizeButtonLabel = resizeButtonLabel;
      }
      $(this).html(resizeButtonLabel);
    })
    
    showGrid() // If the grid was hidden, show it or the page looks blank
    $('.tooltip').hide();
  }); // #tool-clear-map.click()

  $('#tool-settings').on("click", function() {
    $('#tool-settings-options').toggle()
  })

  $('#graphics-quality-low').on("click", function() {
    lowGraphicsMode = $('#graphics-quality-low').prop('checked')
    window.localStorage.setItem('graphicsQualityLow', lowGraphicsMode ? 1 : 0)

    if (lowGraphicsMode) {
      MAX_CANVAS_SIZE = LOW_QUAL_MAX_CANVAS_SIZE
      MAX_SHARDS = LOW_QUAL_MAX_SHARDS
      preferredGridPixelMultiplier = LOW_QUAL_PGPM
      console.log(`Using low graphics mode to improve performance! MAX_CANVAS_SIZE: ${MAX_CANVAS_SIZE} MAX_SHARDS: ${MAX_SHARDS} preferredGridPixelMultiplier: ${preferredGridPixelMultiplier}`)
      MAX_SHARDS
    } else {
      MAX_CANVAS_SIZE = HIGH_QUAL_MAX_CANVAS_SIZE
      MAX_SHARDS = HIGH_QUAL_MAX_SHARDS
      preferredGridPixelMultiplier = HIGH_QUAL_PGPM
      console.log(`Exiting lowGraphicsMode. MAX_CANVAS_SIZE: ${MAX_CANVAS_SIZE} MAX_SHARDS: ${MAX_SHARDS} preferredGridPixelMultiplier: ${preferredGridPixelMultiplier}`)
    }

    var shards = document.getElementById('color-canvas-container').children
    if (shards.length > MAX_SHARDS) {
      for (var x=shards.length;x>MAX_SHARDS;x--) {
        shards[x-1].remove()
      }
    } else {
      if (MMMDEBUG) { console.log("Scaling shards up ...") }
      for (var x=shards.length;x<MAX_SHARDS;x++) {
        $('#color-canvas-container').append(`<canvas id="color-canvas-${x}" width="1600" height="1600" class="hidden color-canvas"></canvas>`)
      }
    }

    colorShardMap = new Set()
    snapCanvasToGrid(true) // Resize all canvases, even though the main is already the correct size
    drawGrid()
    drawCanvas()
  }) // #graphics-quality-low.click()

  $('#rail-line-new').click(function() {
    if ($('#tool-new-line-options').is(':visible')) {
      $(this).children('span').text('Add New Color')
      $('#tool-new-line-options').hide()
    } else {
      $(this).children('span').text('Hide Add Color options')
      $('#tool-new-line-options').show()
    }
  }) // #rail-line-new.click() (expand tool-new-line-options)

  $('#create-new-rail-line').click(function() {

    $('#new-rail-line-name').val($('#new-rail-line-name').val().replaceAll('<', '').replaceAll('>', '').replaceAll('"', '').replaceAll('\\\\', '').replaceAll('/', '-'));

    var allColors = [], allNames = [];
    $('.rail-line').each(function() {
      allColors.push($(this).attr('id').slice(10, 16));
      allNames.push($(this).text());
    });

    if ($('#new-rail-line-color').val() == '') {
      // If a color has not been selected, the line can be created but is undefined.
      // Set it to black instead since that's the default
      $('#new-rail-line-color').val('#000000');
    }

    if (allColors.indexOf($('#new-rail-line-color').val().slice(1, 7)) >= 0) {
      $('#tool-new-line-errors').text('This color already exists! Please choose a new color.');
    } else if (allNames.indexOf($('#new-rail-line-name').val()) >= 0) {
      $('#tool-new-line-errors').text('This color name already exists! Please choose a new name.');
    } else if ($('#new-rail-line-name').val().length == 0) {
      $('#tool-new-line-errors').text('This color name cannot be blank. Please enter a name.');
    } else if ($('#new-rail-line-name').val().length > 100) {
      $('#tool-new-line-errors').text('This color name is too long. Please shorten it.');
    } else if ($('.rail-line').length > 99) {
      $('#tool-new-line-errors').text('Too many colors! Delete your unused ones before creating new ones.');
    } else {
      $('#tool-new-line-errors').text('');
      $('#line-color-options fieldset #line-colors').append('<button id="rail-line-' + $('#new-rail-line-color').val().slice(1, 7) + '" class="rail-line has-tooltip" style="background-color: ' + $('#new-rail-line-color').val() + ';">' + $('#new-rail-line-name').val() + '</button>');
      if (!activeMap['global']) {
        activeMap['global'] = {"lines": {}}
      }
      if (!activeMap['global']['lines']) {
        activeMap['global']['lines'] = {}
      }
      $('.rail-line').each(function() {
        if ($(this).attr('id') != 'rail-line-new') {
          // rail-line-
          activeMap['global']['lines'][$(this).attr('id').slice(10, 16)] = {
            'displayName': $(this).text()
          }
        }
      });
      autoSave(activeMap)
    }
    // Re-bind events to .rail-line -- otherwise, newly created lines won't have events
    bindRailLineEvents();
    resetRailLineTooltips()
    // Repopulate the Edit Rail Lines dropdown menu, in case it's open
    $('#tool-lines-to-change').html('<option>Edit which color?</option>')
    for (var line in activeMap["global"]["lines"]) {
      $('#tool-lines-to-change').append('<option value="' + line + '">' + activeMap["global"]["lines"][line]["displayName"] + '</option>')
    }
    drawCanvas() // This also does a full reset of the color map
  }); // $('#create-new-rail-line').click()

  $('#rail-line-change').click(function() {
    // Expand the options
    if ($('#tool-change-line-options').is(':visible')) {
      $(this).children('span').html('Edit colors &amp; names')
      $('#tool-change-line-options').hide()
    } else {
      $(this).children('span').text('Close Edit Color options')
      $('#tool-change-line-options').show()
    }

    $('#tool-lines-to-change').html('<option>Edit which color?</option>')
    $('#change-line-name').hide()
    $('#change-line-color').hide()
    $('#tool-change-line-options label').hide()
    $('#tool-change-line-options p').text('')

    // Now populate the select dropdown
    for (var line in activeMap["global"]["lines"]) {
      $('#tool-lines-to-change').append('<option value="' + line + '">' + activeMap["global"]["lines"][line]["displayName"] + '</option>')
    }
  }) // #rail-line-change.click()

  $('#tool-lines-to-change').on('change', function() {
    $('#tool-change-line-options label').show()
    // Set the name and color
    if ($('#tool-lines-to-change option:selected').text() != 'Edit which color?') {
      $('#change-line-name').show()
      $('#change-line-color').show()
      $('#change-line-name').val($('#tool-lines-to-change option:selected').text())
      $('#change-line-color').val('#' + $(this).val())
    } else {
      $('#tool-change-line-options p').text('')
      $('#change-line-name').hide()
      $('#change-line-color').hide()
    }
  }) // #tool-lines-to-change.change()

  $('#save-rail-line-edits').click(function() {
    // Save edits
    if ($('#tool-lines-to-change option:selected').text() != 'Edit which color?') {
      var lineColorToChange = $('#tool-lines-to-change').val()
      var lineColorToChangeTo = $('#change-line-color').val().slice(1)
      var lineNameToChange = $('#tool-lines-to-change option:selected').text()
      var lineNameToChangeTo = $('#change-line-name').val().replaceAll('<', '').replaceAll('>', '').replaceAll('"', '').replaceAll('\\\\', '').replaceAll('/', '-') // use same replaces as in $('#create-new-rail-line').click()

      var allNames = [];
      $('.rail-line').each(function() {
        allNames.push($(this).text());
      });

      if ((lineColorToChange != lineColorToChangeTo) && (Object.keys(activeMap["global"]["lines"]).indexOf(lineColorToChangeTo) >= 0)) {
        $('#cant-save-rail-line-edits').text('Can\'t change ' + lineNameToChange + ' - it has the same color as ' + activeMap["global"]["lines"][lineColorToChangeTo]["displayName"])
      }
      else if (allNames.indexOf(lineNameToChangeTo) > -1 && lineNameToChange != lineNameToChangeTo) {
        $('#cant-save-rail-line-edits').text('This color name already exists! Please choose a new name.');
      }
      else {
        replaceColors({
          "color": lineColorToChange,
          "name": lineNameToChange
        }, {
          "color": lineColorToChangeTo,
          "name": lineNameToChangeTo
        })
        $('#rail-line-change span').html('Edit colors &amp; names')
        $('#cant-save-rail-line-edits').text('')
        $('#tool-change-line-options').hide()
        // If the line tool is in use, unset it so we don't get a stale color
        if (activeTool == 'line') {
          setActiveTool('look')
          $('#tool-line').attr('style', '')
          $('#tool-line').removeClass('active')
        } // if line
      } // else
    } // # not Edit which color?
    // If replacing the active line, change the active color too
    // or you'll end up drawing with a color that no longer exists among the globals
    if (activeTool == 'line' && rgb2hex(activeToolOption).slice(1, 7) == lineColorToChange)
      activeToolOption = '#' + lineColorToChangeTo
    resetRailLineTooltips()
    drawCanvas() // This also does a full reset of the color map
  }) // #save-rail-line-edits.click()

  $('#tool-map-style').on('click', function() {
    $('#tool-map-style-options').toggle()
    if (!$('#tool-map-style-options').is(':visible')) {
      $('#tool-map-style').removeClass('active')
    }
    $('.tooltip').hide();
    if (mapLineWidth == 0.75) {
      $('#tool-map-style-line-750').addClass('active-mapstyle')
    } else {
      $('#tool-map-style-line-' + (mapLineWidth * 1000)).addClass('active-mapstyle')
    }
    $('#tool-map-style-station-' + mapStationStyle).addClass('active-mapstyle')
  })

  $('.map-style-line').on('click', function() {
    if ($(this).attr('id') == 'tool-map-style-line-750') {
      var chosenWidth = 0.75
    } else {
      var chosenWidth = 1 / parseInt($(this).data('line-width-divisor'))
    }
    if (selectedPoints.length > 0) {
      for (xy of selectedPoints) {
        var x = xy[0]
        var y = xy[1]
        var clws = getActiveLine(x, y, activeMap, true)
        if (!clws) {
          continue
        }
        var color = clws[0]
        var lws = clws[1]

        // Not using updateMapObject here, because it presumes the activeLineWidthStyle;
        //  handle it manually
        var oldWidth = lws.split("-1")[0]
        if (oldWidth == chosenWidth) {
          continue
        }
        var style = lws.split("-")[1]
        var newLws = chosenWidth + "-" + style
        if (!activeMap["points_by_color"][color][newLws]) {
          activeMap["points_by_color"][color][newLws] = {}
        }
        if (!activeMap["points_by_color"][color][newLws][x]) {
          activeMap["points_by_color"][color][newLws][x] = {}
        }
        delete activeMap["points_by_color"][color][lws][x][y]
        activeMap["points_by_color"][color][newLws][x][y] = 1
      }
      drawCanvas(activeMap)
      autoSave(activeMap)
      return
    }

    mapLineWidth = chosenWidth
    $('.map-style-line.active-mapstyle').removeClass('active-mapstyle')
    $(this).addClass('active-mapstyle')
    if (activeMap && activeMap['global'] && activeMap['global']['style']) {
      activeMap['global']['style']['mapLineWidth'] = mapLineWidth
    } else if (activeMap && activeMap['global']) {
      activeMap['global']['style'] = {
        'mapLineWidth': mapLineWidth
      }
    }
    if (mapDataVersion >= 3) {
      // Since restyleAllLines calls drawCanvas, I don't need to here.
      restyleAllLines(mapLineWidth)
    } else {
      drawCanvas(activeMap)
    }
    autoSave(activeMap)
  })

  $('.map-style-station').on('click', function() {
    var chosenStationStyle = $(this).data('station-style')
    if (selectedPoints.length > 0) {
      for (xy of selectedPoints) {
        var x = xy[0]
        var y = xy[1]
        if (!activeMap["stations"][x] || !activeMap["stations"][x][y]) {
          continue
        }
        activeMap["stations"][x][y]["style"] = chosenStationStyle
      }
      autoSave(activeMap)
      drawCanvas(activeMap)
      return
    }
    mapStationStyle = chosenStationStyle
    $('.map-style-station.active-mapstyle').removeClass('active-mapstyle')
    $(this).addClass('active-mapstyle')
    $('#reset-all-station-styles').text('Set ALL stations to ' + $(this).text())
    if (activeMap && activeMap['global'] && activeMap['global']['style']) {
      activeMap['global']['style']['mapStationStyle'] = mapStationStyle
    } else if (activeMap && activeMap['global']) {
      activeMap['global']['style'] = {
        'mapStationStyle': mapStationStyle
      }
    }
    autoSave(activeMap)
    drawCanvas()
  })

  $('#station-name').change(function() {
    var x = $('#station-coordinates-x').val();
    var y = $('#station-coordinates-y').val();

    if (Object.keys(temporaryStation).length > 0) {
      if (mapDataVersion == 2 || mapDataVersion == 3) {
        if (!activeMap["stations"]) { activeMap["stations"] = {} }
        if (!activeMap["stations"][x]) { activeMap["stations"][x] = {} }
        activeMap["stations"][x][y] = Object.assign({}, temporaryStation)
      } else {
        activeMap[x][y]["station"] = Object.assign({}, temporaryStation)
      }
      temporaryStation = {}
    }

    metroMap = updateMapObject(x, y, "name", $('#station-name').val())
    autoSave(metroMap);
    drawCanvas(metroMap, true);
  }); // $('#station-name').change()

  $('#station-name-orientation').change(function() {
    var x = $('#station-coordinates-x').val();
    var y = $('#station-coordinates-y').val();

    var orientation = parseInt($(this).val())

    if (x >= 0 && y >= 0) {
      if (orientation == 0) {
        if (Object.keys(temporaryStation).length > 0) {
          temporaryStation["orientation"] = 0
        } else {
          if (mapDataVersion == 2 || mapDataVersion == 3)
            activeMap["stations"][x][y]["orientation"] = 0
          else if (mapDataVersion == 1)
            activeMap[x][y]["station"]["orientation"] = 0
        }
      } else if (ALLOWED_ORIENTATIONS.indexOf(orientation) >= 0) {
        if (Object.keys(temporaryStation).length > 0) {
          temporaryStation["orientation"] = orientation
        } else {
          if (mapDataVersion == 2 || mapDataVersion == 3)
            activeMap["stations"][x][y]["orientation"] = orientation
          else if (mapDataVersion == 1)
            activeMap[x][y]["station"]["orientation"] = orientation
        } // else (not temporaryStation)
      } // else if ALLOWED_ORIENTATION
    } // if x >= 0 && y >= 0

    window.localStorage.setItem('metroMapStationOrientation', orientation);
    if (Object.keys(temporaryStation).length == 0) {
      autoSave(activeMap);
    }
    drawCanvas(activeMap, true);
    drawIndicator(x, y);
  }); // $('#station-name-orientation').change()

  $('#station-style').on('change', function() {
    var x = $('#station-coordinates-x').val()
    var y = $('#station-coordinates-y').val()

    var thisStationStyle = $(this).val()

    if (x >= 0 && y >= 0) {
      if (ALLOWED_STYLES.indexOf(thisStationStyle) >= 0) {
        if (Object.keys(temporaryStation).length > 0) {
          temporaryStation["style"] = thisStationStyle
        } else {
          if (mapDataVersion == 2 || mapDataVersion == 3)
            activeMap["stations"][x][y]["style"] = thisStationStyle
          else if (mapDataVersion == 1)
            activeMap[x][y]["station"]["style"] = thisStationStyle
        } // else (not temporaryStation)
      } else if (!thisStationStyle) {
        if ((mapDataVersion == 2 || mapDataVersion == 3) && activeMap['stations'][x][y]['style']) {
          delete activeMap['stations'][x][y]['style']
        } else if (mapDataVersion == 1 && activeMap[x][y]['station']['style']) {
          delete activeMap[x][y]['station']['style']
        }
      }// else if ALLOWED_STYLES
    } // if x >= 0 && y >= 0

    if (Object.keys(temporaryStation).length == 0) {
      autoSave(activeMap);
    }
    drawCanvas(activeMap, true);
    drawIndicator(x, y);
  }); // $('#station-style').change()

  $('#station-transfer').click(function() {
    var x = $('#station-coordinates-x').val();
    var y = $('#station-coordinates-y').val();
    if (x >= 0 && y >= 0 ) {
      if ($(this).is(':checked')) {
        if (Object.keys(temporaryStation).length > 0) {
         temporaryStation["transfer"] = 1
        } else {
          if (mapDataVersion == 2 || mapDataVersion == 3)
            activeMap["stations"][x][y]["transfer"] = 1
          else if (mapDataVersion == 1)
            activeMap[x][y]["station"]["transfer"] = 1
        }
      } else {
        if (Object.keys(temporaryStation).length > 0) {
          delete temporaryStation["transfer"] 
        } else {
          if (mapDataVersion == 2 || mapDataVersion == 3)
            delete activeMap["stations"][x][y]["transfer"]
          else if (mapDataVersion == 1)
            delete activeMap[x][y]["station"]["transfer"]
        } // else (temporaryStation is blank)
      } // else (not checked)
    } // if x >= 0 && y >= 0

    if (Object.keys(temporaryStation).length == 0) {
      autoSave(activeMap)
    }
    drawCanvas(activeMap, true)
    drawIndicator(x, y);
  }); // $('#station-transfer').click()
  $('#loading').remove()
}); // document.ready()

// Cheat codes / Advanced map manipulations
function getSurroundingLine(x, y, metroMap, returnLineWidthStyle) {
  // Returns a line color only if x,y has two neighbors
  //  with the same color going in the same direction
  // Important: this can't return early if there's no point at x, y
  //  because when stretching a map, there won't be anything there,
  //  and the point is to ensure that I'm finding the two points around this.
  // Additionally, I can't modify the conditionals below
  //  to ensure that the color at x, y is the same as its surrounding points,
  //  and for the same reason.

  x = parseInt(x)
  y = parseInt(y)

  if (getActiveLine(x-1, y, metroMap) && (getActiveLine(x-1, y, metroMap) == getActiveLine(x+1, y, metroMap))) {
    // Left and right match
    return getActiveLine(x-1, y, metroMap, returnLineWidthStyle);
  } else if (getActiveLine(x, y-1, metroMap) && (getActiveLine(x, y-1, metroMap) == getActiveLine(x, y+1, metroMap))) {
    // Top and bottom match
    return getActiveLine(x, y-1, metroMap, returnLineWidthStyle);
  } else if (getActiveLine(x-1, y-1, metroMap) && (getActiveLine(x-1, y-1, metroMap) == getActiveLine(x+1, y+1, metroMap))) {
    // Diagonal: \
    return getActiveLine(x-1, y-1, metroMap, returnLineWidthStyle);
  } else if (getActiveLine(x-1, y+1, metroMap) && (getActiveLine(x-1, y+1, metroMap) == getActiveLine(x+1, y-1, metroMap))) {
    // Diagonal: /
    return getActiveLine(x-1, y+1, metroMap, returnLineWidthStyle);
  }
} // getSurroundingLine(x, y, metroMap, returnLineWidthStyle)

function setAllStationOrientations(metroMap, orientation) {
  // Set all station orientations to a certain direction
  orientation = parseInt(orientation)
  if (ALLOWED_ORIENTATIONS.indexOf(orientation) == -1)
    return

  if (selectedPoints.length > 0) {
    for (xy of selectedPoints) {
      var x = xy[0]
      var y = xy[1]
      if (!metroMap["stations"][x] || !metroMap["stations"][x][y]) {
        continue
      }
      metroMap["stations"][x][y]["orientation"] = orientation
    }
    return
  }

  if (mapDataVersion == 2 || mapDataVersion == 3) {
    for (var x in metroMap['stations']) {
      for (var y in metroMap['stations'][x]) {
        x = parseInt(x);
        y = parseInt(y);
        metroMap['stations'][x][y]["orientation"] = orientation
      }
    }
  } else if (mapDataVersion == 1) {
    for (var x in metroMap) {
      for (var y in metroMap[x]) {
        x = parseInt(x);
        y = parseInt(y);
        if (!Number.isInteger(x) || !Number.isInteger(y))
          continue
        if (Object.keys(metroMap[x][y]).indexOf('station') == -1)
          continue
        metroMap[x][y]["station"]["orientation"] = orientation
      } // for y
    } // for x
  } // mapDataVersion
} // setAllStationOrientations(metroMap, orientation)
$('#set-all-station-name-orientation').on('click', function() {
  var orientation = $('#set-all-station-name-orientation-choice').val()
  setAllStationOrientations(activeMap, orientation)
  autoSave(activeMap)
  drawCanvas()
  setTimeout(function() {
    $('#set-all-station-name-orientation').removeClass('active')
  }, 500)
})

function resetAllStationStyles(metroMap) {

  if (selectedPoints.length > 0) {
    for (xy of selectedPoints) {
      var x = xy[0]
      var y = xy[1]
      if (!metroMap["stations"][x] || !metroMap["stations"][x][y]) {
        continue
      }
      delete metroMap["stations"][x][y]["style"]
    }
    return
  }

  if (mapDataVersion == 2 || mapDataVersion == 3) {
    for (var x in metroMap['stations']) {
      for (var y in metroMap['stations'][x]) {
        x = parseInt(x);
        y = parseInt(y);
        if (metroMap['stations'][x][y]['style']) {
          delete metroMap['stations'][x][y]["style"]
        }
      }
    }
  } else if (mapDataVersion == 1) {
    for (var x in metroMap) {
      for (var y in metroMap[x]) {
        x = parseInt(x);
        y = parseInt(y);
        if (!Number.isInteger(x) || !Number.isInteger(y))
          continue
        if (Object.keys(metroMap[x][y]).indexOf('station') == -1)
          continue
        if (Object.keys(metroMap[x][y]['station']).indexOf('style') == -1)
          continue
        delete metroMap[x][y]["station"]["style"]
      }
    }
  }
}
$('#reset-all-station-styles').on('click', function() {
  resetAllStationStyles(activeMap)
  autoSave(activeMap)
  drawCanvas()
  setTimeout(function() {
    $('#reset-all-station-styles').removeClass('active')
  }, 500)
})

function combineLineColorWidthStyle(value) {
  if (typeof value === 'object') { // mapDataVersion >= 3
    return value.join('-')
  }
  return value
}

function getLineDirection(x, y, metroMap) {
  // Returns which direction this line is going in,
  // to help draw the positioning of new-style stations
  x = parseInt(x)
  y = parseInt(y)

  origin = combineLineColorWidthStyle(getActiveLine(x, y, metroMap, (mapDataVersion >= 3)))
  NW = combineLineColorWidthStyle(getActiveLine(x-1, y-1, metroMap, (mapDataVersion >= 3)))
  NE = combineLineColorWidthStyle(getActiveLine(x+1, y-1, metroMap, (mapDataVersion >= 3)))
  SW = combineLineColorWidthStyle(getActiveLine(x-1, y+1, metroMap, (mapDataVersion >= 3)))
  SE = combineLineColorWidthStyle(getActiveLine(x+1, y+1, metroMap, (mapDataVersion >= 3)))
  N = combineLineColorWidthStyle(getActiveLine(x, y-1, metroMap, (mapDataVersion >= 3)))
  E = combineLineColorWidthStyle(getActiveLine(x+1, y, metroMap, (mapDataVersion >= 3)))
  S = combineLineColorWidthStyle(getActiveLine(x, y+1, metroMap, (mapDataVersion >= 3)))
  W = combineLineColorWidthStyle(getActiveLine(x-1, y, metroMap, (mapDataVersion >= 3)))

  info = {
    "direction": false,
    "offset_endcap": false,
    "endcap": false
  }

  if (!origin) {
    return info
  }

  var neighboringPoints = [N, E, S, W, NE, SE, SW, NW].filter((d) => d !== undefined && d == origin)
  if (neighboringPoints.length == 1) {
    info['endcap'] = true
    if ([S, E, SE, SW].filter((d) => d !== undefined).length == 1) {
      // London styles need these endcaps drawn at a slightly different offset
      // Note: these are the N, W, NE, NW endcaps; the points I'm checking are their neighboring points
      info['offset_endcap'] = true
    }
  }

  if (origin == W && W == E) {
    info['direction'] = 'horizontal'
  } else if (origin == N && N == S) {
    info['direction'] = 'vertical'
  } else if (origin == NW && NW == SE) {
    info['direction'] = 'diagonal-se'
  } else if (origin == SW && SW == NE) {
    info['direction'] = 'diagonal-ne'
  } else if (origin == W || origin == E) {
    info['direction'] = 'horizontal'
  } else if (origin == N || origin == S) {
    info['direction'] = 'vertical'
  } else if (origin == NW || origin == SE) {
    info['direction'] = 'diagonal-se'
  } else if (origin == SW || origin == NE) {
    info['direction'] = 'diagonal-ne'
  } else {
    info['direction'] = 'singleton'
  }

  return info
}

function stationIsStyle(station, style) {
  if (station && station['style'] && station['style'] == style) {
    // Return true if station is explicitly the given style,
    return true
  } else if (station && !station['style'] && mapStationStyle == style) {
    //  or implicitly because the station is the default and there's a style set
    return true
  }
  return false
} // stationIsStyle(station, style)

function getConnectedStations(x, y, metroMap, londonConnections) {
  // Finds connecting stations along a SINGLE direction,
  //  to aid in drawing one continuous station from multiple stations.
  // If applicable, returns a set of starting and ending x,y coordinates

  // If londonConnections is true, return all connected transfer stations
  //  along all directions

  // Known issue:
  // If you have several stations set up along multiple directions, for example:
  // SSSS
  // S <---------
  // S <---------
  //    Then the stations with arrows won't be drawn.
  // This is because the upper-leftmost station
  //  identifies its longest connection left to right (4) and not up to down (3)
  // The stations below have their longest connection up to down (3),
  // but are considered "interior" to the upper-leftmost,
  // and the stations aren't drawn to avoid overpainting.
  // Fixing this would add a lot of complexity to a function that's already a lag on performance,
  //  and in truth it's a weird use case.
  // Workaround: If you want the arrowed stations to appear, use other station shapes for them.

  x = parseInt(x)
  y = parseInt(y)

  // Drawing happens top -> down,
  // then left -> right.
  // So if a station is adjacent to another
  // on a side that's already been drawn,
  // (W, N, NW, SW)
  // don't draw this station,
  // only draw S, E, SE, NE

  var origin = getStation(x, y, metroMap)

  if (!origin) {
    return
  }
  if (londonConnections && (!origin || !origin['transfer'])) {
    return
  }

  var NW = getStation(x-1, y-1, metroMap)
  var NE = getStation(x+1, y-1, metroMap)
  var SW = getStation(x-1, y+1, metroMap)
  var SE = getStation(x+1, y+1, metroMap)
  var N = getStation(x, y-1, metroMap)
  var E = getStation(x+1, y, metroMap)
  var S = getStation(x, y+1, metroMap)
  var W = getStation(x-1, y, metroMap)

  if (!NW && !NE && !SW && !SE && !N && !E && !S && !W) {
    return 'singleton'
  }

  if (londonConnections) {
    var connectedTo = {}

    if (stationIsStyle(NW, 'london') && NW['transfer']) { connectedTo["NW"] = [x-1, y-1] }
    if (stationIsStyle(NE, 'london') && NE['transfer']) { connectedTo["NE"] = [x+1, y-1] }
    if (stationIsStyle(SW, 'london') && SW['transfer']) { connectedTo["SW"] = [x-1, y+1] }
    if (stationIsStyle(SE, 'london') && SE['transfer']) { connectedTo["SE"] = [x+1, y+1] }
    if (stationIsStyle(N, 'london') && N['transfer']) { connectedTo["N"] = [x, y-1] }
    if (stationIsStyle(E, 'london') && E['transfer']) { connectedTo["E"] = [x+1, y] }
    if (stationIsStyle(S, 'london') && S['transfer']) { connectedTo["S"] = [x, y+1] }
    if (stationIsStyle(W, 'london') && W['transfer']) { connectedTo["W"] = [x-1, y] }

    return connectedTo
  }

  function shouldUseOvals(station) {
    // Note: This conditional is different than in drawPoint, because in drawPoint
    //  we're drawing the lines
    if (!station) { return false }
    if (station['style'] == 'rect' || station['style'] == 'rect-round' || station['style'] == 'circles-thin')
      return true
    else if (!station['style'] && (mapStationStyle == 'rect' || mapStationStyle == 'rect-round' || mapStationStyle == 'circles-thin'))
      return true
    return false
  }

  // Starting and ending coordinates for this oval station
  var coordinates = {
    "highest": {
      'E': 0,
      'S': 0,
      'SE': 0,
      'NE': 0
    },
    'E': {},
    'S': {},
    'N': {},
    'W': {},
    'NE': {},
    'SE': {},
    'SW': {},
    'NW': {}
  }

  if (E && shouldUseOvals(E)) {
    var xn = x
    var yn = y
    do {
      xn += 1
    } while (shouldUseOvals(getStation(xn, yn, metroMap)))
    coordinates['E'] = {
      'x1': xn - 1,
      'y1': yn
    }
    coordinates['highest']['E'] = (xn - x) - 1
  }
  if (S && shouldUseOvals(S)) {
    var xn = x
    var yn = y
    do {
      yn += 1
    } while (shouldUseOvals(getStation(xn, yn, metroMap)))
    coordinates['S'] = {
      'x1': xn,
      'y1': yn - 1
    }
    coordinates['highest']['S'] = (yn - y) - 1
  }
  if (NE && shouldUseOvals(NE)) {
    var xn = x
    var yn = y
    do {
      xn += 1
      yn -= 1
    } while (shouldUseOvals(getStation(xn, yn, metroMap)))
    coordinates['NE'] = {
      'x1': xn - 1,
      'y1': yn + 1
    }
    coordinates['highest']['NE'] = (xn - x) - 1
  }
  if (SE && shouldUseOvals(SE)) {
    var xn = x
    var yn = y
    do {
      xn += 1
      yn += 1
    } while (shouldUseOvals(getStation(xn, yn, metroMap)))
    coordinates['SE'] = {
      'x1': xn - 1,
      'y1': yn - 1
    }
    coordinates['highest']['SE'] = (xn - x) - 1
  }

  // Next check W, N, NW, SW -- if we find anything here,
  //  add those totals to E, S, SE, NE and flag that we're internal
  if (W && shouldUseOvals(W)) {
    var xn = x
    var yn = y
    do {
      xn -= 1
    } while (shouldUseOvals(getStation(xn, yn, metroMap)))
    coordinates['W'] = {
      'x1': xn + 1,
      'y1': yn
    }
    coordinates['E']['internal'] = true
    coordinates['highest']['E'] += Math.abs(xn - x) - 1
  }
  if (N && shouldUseOvals(N)) {
    var xn = x
    var yn = y
    do {
      yn -= 1
    } while (shouldUseOvals(getStation(xn, yn, metroMap)))
    coordinates['N'] = {
      'x1': xn,
      'y1': yn + 1
    }
    coordinates['S']['internal'] = true
    coordinates['highest']['S'] += Math.abs(yn - y) - 1
  }
  if (NW && shouldUseOvals(NW)) {
    var xn = x
    var yn = y
    do {
      xn -= 1
      yn -= 1
    } while (shouldUseOvals(getStation(xn, yn, metroMap)))
    coordinates['NW'] = {
      'x1': xn + 1,
      'y1': yn + 1
    }
    coordinates['SE']['internal'] = true
    coordinates['highest']['SE'] += Math.abs(xn - x) - 1
  }
  if (SW && shouldUseOvals(SW)) {
    var xn = x
    var yn = y
    do {
      xn -= 1
      yn += 1
    } while (shouldUseOvals(getStation(xn, yn, metroMap)))
    coordinates['SW'] = {
      'x1': xn + 1,
      'y1': yn - 1
    }
    coordinates['NE']['internal'] = true
    coordinates['highest']['NE'] += Math.abs(xn - x) - 1
  }

  var numConnections = Object.values(coordinates['highest']).filter((n) => n > 0)
  var mostStations = Math.max(...Object.values(numConnections))

  if (numConnections.length == 0) {
    return 'singleton'
  }

  if (numConnections.indexOf(mostStations) != numConnections.lastIndexOf(mostStations)) {
    // More than one direction has an equal (highest) number of connecting stations
    return 'conflicting'
  }

  var longestConnection = Object.keys(coordinates['highest']).filter((n) => Number.isNaN(n) !== true).sort(function(a,b){return coordinates['highest'][a]-coordinates['highest'][b]}).reverse()

  if (longestConnection && longestConnection[0]) {
    if (coordinates[longestConnection[0]]['internal']) {
      return false
    }
    return {
      'x0': x,
      'y0': y,
      'x1': coordinates[longestConnection[0]]['x1'],
      'y1': coordinates[longestConnection[0]]['y1']
    }
  }

  return true // Draw, it's not a connected station
}

function stretchMap(metroMapObject) {
  // Stretch out a map
  // First, loop through all the keys and multiply them by 2
  // Next, loop through all the spaces and check:
  //   is that space surrounded by similar neighbors?
  //   if so, set that space equal to the color of its neighbors

  if (selectedPoints.length > 0) {
    // Disable the selection, it's not relevant now
    selectedPoints = []
    clearMarchingAnts()
  }

  if (!metroMapObject) {
    metroMapObject = activeMap;
  }

  var newMapObject = {};
  newMapObject['global'] = Object.assign({}, activeMap['global'])
  if (mapDataVersion == 3) {
    newMapObject['points_by_color'] = {}
    for (var color in metroMapObject['points_by_color']) {
      newMapObject['points_by_color'][color] = {}
      for (var lineWidthStyle in metroMapObject['points_by_color'][color]) {
        newMapObject['points_by_color'][color][lineWidthStyle] = {}
        for (var x in metroMapObject['points_by_color'][color][lineWidthStyle]) {
          for (var y in metroMapObject['points_by_color'][color][lineWidthStyle][x]) {
            x = parseInt(x)
            y = parseInt(y)
            if (!metroMapObject['points_by_color'][color][lineWidthStyle][x][y]) {
              continue
            }
            if (x * 2 > MAX_MAP_SIZE-1 || y * 2 > MAX_MAP_SIZE-1) {
              continue
            }
            if (!newMapObject['points_by_color'][color][lineWidthStyle].hasOwnProperty(x * 2)) {
              newMapObject['points_by_color'][color][lineWidthStyle][x * 2] = {}
            }
            newMapObject['points_by_color'][color][lineWidthStyle][x * 2][y * 2] = metroMapObject['points_by_color'][color][lineWidthStyle][x][y]
          } // for y
        } // for x
      } // for lineWidthStyle
    } // for color

    // Set the gridRows and gridCols
    setMapSize(newMapObject)
    resetResizeButtons(gridCols)

    newMapObject['stations'] = {}
    for (var x in metroMapObject['stations']) {
      for (var y in metroMapObject['stations'][x]) {
        x = parseInt(x)
        y = parseInt(y)
        if (x * 2 >= gridRows || y * 2 >= gridCols) {
          // Prevent orphaned stations
          continue
        }
        if (!newMapObject['stations'].hasOwnProperty(x * 2)) {
          newMapObject['stations'][x * 2] = {}
        }
        newMapObject['stations'][x * 2][y * 2] = Object.assign({}, metroMapObject['stations'][x][y])
      }
    }

    // Fill in the newly created in-between spaces
    for (var x=1;x<gridRows;x++) {
      for (var y=1;y<gridCols;y++) {
        var colorLineWidthStyle = getSurroundingLine(x, y, newMapObject, true)
        if (!colorLineWidthStyle) { continue }
        var color = colorLineWidthStyle[0]
        var lineWidthStyle = colorLineWidthStyle[1]
        if (!newMapObject['points_by_color'][color][lineWidthStyle]) {
          newMapObject['points_by_color'][color][lineWidthStyle] = {}
        }
        if (!newMapObject['points_by_color'][color][lineWidthStyle].hasOwnProperty(x)) {
          newMapObject['points_by_color'][color][lineWidthStyle][x] = {}
        }
        newMapObject['points_by_color'][color][lineWidthStyle][x][y] = 1
      } // for y
    } // for x
  } else if (mapDataVersion == 2) {
    newMapObject['points_by_color'] = {}
    for (var color in metroMapObject['points_by_color']) {
      newMapObject['points_by_color'][color] = {'xys': {}}
      for (var x in metroMapObject['points_by_color'][color]['xys']) {
        for (var y in metroMapObject['points_by_color'][color]['xys'][x]) {
          x = parseInt(x)
          y = parseInt(y)
          if (!metroMapObject['points_by_color'][color]['xys'][x][y]) {
            continue
          }
          if (x * 2 > MAX_MAP_SIZE-1 || y * 2 > MAX_MAP_SIZE-1) {
            continue
          }
          if (!newMapObject['points_by_color'][color]['xys'].hasOwnProperty(x * 2)) {
            newMapObject['points_by_color'][color]['xys'][x * 2] = {}
          }
          newMapObject['points_by_color'][color]['xys'][x * 2][y * 2] = metroMapObject['points_by_color'][color]['xys'][x][y]
        } // for y
      } // for x
    } // for color

    // Set the gridRows and gridCols
    setMapSize(newMapObject)
    resetResizeButtons(gridCols)

    newMapObject['stations'] = {}
    for (var x in metroMapObject['stations']) {
      for (var y in metroMapObject['stations'][x]) {
        x = parseInt(x)
        y = parseInt(y)
        if (x * 2 >= gridRows || y * 2 >= gridCols) {
          // Prevent orphaned stations
          continue
        }
        if (!newMapObject['stations'].hasOwnProperty(x * 2)) {
          newMapObject['stations'][x * 2] = {}
        }
        newMapObject['stations'][x * 2][y * 2] = Object.assign({}, metroMapObject['stations'][x][y])
      }
    }

    // Fill in the newly created in-between spaces
    for (var x=1;x<gridRows;x++) {
      for (var y=1;y<gridCols;y++) {
        var color = getSurroundingLine(x, y, newMapObject)
        if (!color) { continue }
        if (!newMapObject['points_by_color'][color]['xys'].hasOwnProperty(x)) {
          newMapObject['points_by_color'][color]['xys'][x] = {}
        }
        newMapObject['points_by_color'][color]['xys'][x][y] = 1
      } // for y
    } // for x
  } else if (mapDataVersion == 1) {
    for (var x in metroMapObject) {
      for (var y in metroMapObject[x]) {
        x = parseInt(x);
        y = parseInt(y);
        if (!Number.isInteger(x) || !Number.isInteger(y)) {
          continue;
        }
        if (!newMapObject.hasOwnProperty(x * 2)) {
          newMapObject[x * 2] = {}
        }
        newMapObject[x * 2][y * 2] = metroMapObject[x][y];
      } // for y
    } // for x

    // Set the gridRows and gridCols
    setMapSize(newMapObject)
    resetResizeButtons(gridCols)

    // Fill in the newly created in-between spaces
    for (var x=1;x<gridRows;x++) {
      for (var y=1;y<gridCols;y++) {
        var surroundingLine = getSurroundingLine(x, y, newMapObject);
        if (surroundingLine) {
          if (!newMapObject.hasOwnProperty(x)) {
            newMapObject[x] = {}
          }
          newMapObject[x][y] = {
            "line": surroundingLine
          }
        } // if neighboringLine
      } // for y
    } // for x
  } // mapDataVersion
  
  activeMap = newMapObject
  autoSave(activeMap)
  loadMapFromObject(newMapObject);
  drawCanvas(newMapObject);
  return newMapObject;
} // stretchMap(metroMapObject)

function replaceColors(color1, color2) {
    // Replaces all instances of color1 with color2.
    // Expects objects with keys name and color
    var savedMapData = JSON.stringify(activeMap);
    if (typeof color1 == 'object') {
      if (color1.name && color2.name) {
        if (color1.color) {
          $('#rail-line-' + color1.color).text(color2.name)
        }
        savedMapData = savedMapData.replaceAll('"displayName":"' + color1.name + '"', '"displayName":"' + color2.name + '"');
      }
      if (color1.color && color2.color && color1.color.match('[a-fA-F0-9]{6}') && color2.color.match('[a-fA-F0-9]{6}')) {
        savedMapData = savedMapData.replaceAll('"' + color1.color + '"', '"' + color2.color + '"');
      }
      if (color1.color != color2.color) {
        $('#rail-line-' + color1.color).remove()
      }
    } else {
      return
    }

    savedMapData = JSON.parse(savedMapData);

    // Fix problem where renaming a line would not 'stick'
    if (savedMapData["global"]["lines"][color1.color] &&
        typeof color2 == 'object' && color2.name) {
      savedMapData["global"]["lines"][color1.color]["displayName"] = color2.name
    }

    activeMap = savedMapData;
    loadMapFromObject(activeMap);
    drawCanvas(activeMap);
    autoSave(activeMap);
} // replaceColors(color1, color2)

// Steer mobile users toward the gallery, for a better experience
function editOnSmallScreen() {
  $('#mobile-header').removeClass('visible-xs') // otherwise .hide won't take effect
  $('#mobile-header').hide()
  $('#mobile-header').css({"height": 0}) // otherwise the canvas is all messed up

  $('#controls').removeClass('hidden-xs');

  collapseToolbox()
  $('#snap-controls-left').trigger('click')

  if ($('#tool-line').prop('disabled')) {
    $('#tool-export-canvas').click()
  }
  $('#grid-canvas').show();
  $('#hover-canvas').show();
  $('#ruler-canvas').show();
  $('#metro-map-canvas').show();
  $('#metro-map-stations-canvas').show();
  $('#metro-map-image').hide()

  // Needed if not viewing a specific map
  $('#canvas-container').removeClass('hidden-xs');
  snapCanvasToGrid();
  drawGrid()

  drawCanvas();
} // editOnSmallScreen

$('#try-on-mobile').click(function() {
  editOnSmallScreen()
});

$('#i-am-on-desktop').on('click', function() {
  editOnSmallScreen()
  $('#tool-export-canvas').remove()
  $('#tool-download-image').removeClass('hidden-xs')
  // Consider: Set localStorage; but what if someone clicks this by mistake?
})

function collapseToolbox() {
  // When collapsed, the toolbox is pretty small -- too small really to be able to read
  //  any of the buttons like Move, Resize, or Style.
  // So when collapsed, hide those altogether.

  if (menuIsCollapsed) { return }
  menuIsCollapsed = true
  $('#controls').addClass('collapsed')

  // CONSIDER: Can replace most of these hide/shows here and in expandToolbox with editing index.html to use the .hide-when-collapsed class

  $('#toolbox button span.button-label').hide()
  $('#title, #remix, #credits, #rail-line-new, #tool-new-line-options, #line-style-options, #rail-line-change, #tool-change-line-options, #rail-line-delete, #straight-line-assist-options, #flood-fill-options, #tool-move-all, #tool-move-options, #tool-resize-all, #tool-resize-options, #tool-map-style, #tool-map-style-options, #name-map, #name-this-map').hide()
  $('#controls-collapse-menu').hide()
  $('#tool-line-caption-draw').hide()
  $('#tool-eraser-caption-eraser').hide()
  $('#tool-line-caption-fill').hide()
  $('#tool-eraser-caption-fill').hide()
  if ($('#hide-save-share-url').length == 1) {
    $('#hide-save-share-url').hide()
  }
  $('#rail-line-new').children('span').text('Add New Color')
  $('#rail-line-change').children('span').html('Edit colors &amp; names')
  $('#controls-expand-menu').show()
}

function expandToolbox() {
  if (!menuIsCollapsed) { return }
  menuIsCollapsed = false
  $('#controls').removeClass('collapsed')

  var activeColor = $('#tool-line').attr('style')
  if (activeColor) {
    $('#tool-line').attr('style', activeColor)
  }

  // Remember whether it's on the left side of the screen
  if ($('#controls').attr('style') && $('#controls').attr('style').indexOf("left: 5px") > -1) {
    $('#snap-controls-left').hide()
  } else {
    $('#snap-controls-right').hide()
  }

  $('#toolbox button span.button-label').show()
  $('#title, #remix, #credits, #rail-line-new, #rail-line-change, #rail-line-delete, #straight-line-assist-options, #flood-fill-options, #tool-move-all, #tool-resize-all').show()

  // -----------------------------------------------
  // Not all features are available in every version

  if (mapDataVersion >= 2) {
    $('#tool-map-style').show()
  }

  if (mapDataVersion >= 3) {
    $('#line-style-options').show()
  }
  // -----------------------------------------------

  $('#tool-move-all, #tool-resize-all').removeClass('width-100')

  if ($('#tool-flood-fill').prop('checked')) {
    $('#tool-line-caption-draw').hide()
    $('#tool-eraser-caption-eraser').hide()
  } else {
    $('#tool-line-caption-fill').hide()
    $('#tool-eraser-caption-fill').hide()
  }

  if ($('#hide-save-share-url').length == 1) {
    $('#hide-save-share-url').show()
  }

  if ($('#name-this-map').text() == 'Name this map') {
    $('#name-map, #name-this-map').show()
  }

  $('#controls-collapse-menu').show()
  $('#controls-expand-menu').hide()
}

$('#controls-collapse-menu').on('click', collapseToolbox)
$('#controls-expand-menu').on('click', expandToolbox)

function colorInUse(color) {
  if (!activeMap || !activeMap['points_by_color'] || !activeMap['points_by_color'][color]) {
    return false
  }
  if (mapDataVersion == 3) {
    for (var lineWidthStyle in activeMap['points_by_color'][color]) {
      for (var x in activeMap['points_by_color'][color][lineWidthStyle]) {
        for (var y in activeMap['points_by_color'][color][lineWidthStyle][x]) {
          if (activeMap['points_by_color'][color][lineWidthStyle][x][y]) {
            return true
          } // if there's actually a point here, not just one that was deleted
        } // y
      } // x
    } // lineWidthStyle
  } else if (mapDataVersion == 2) {
    if (!activeMap['points_by_color'][color]['xys']) { return }
    for (var x in activeMap['points_by_color'][color]['xys']) {
      for (var y in activeMap['points_by_color'][color]['xys'][x]) {
        if (activeMap['points_by_color'][color]['xys'][x][y]) {
          return true
        } // if there's actually a point here, not just one that was deleted
      } // y
    } // x
  } // mapDataVersion
} // colorInUse(color)

$('.line-style-choice-width').on('click', function() {
  $('.line-style-choice-width').removeClass('active')
  $('.line-style-choice-width.active-mapstyle').removeClass('active-mapstyle')
  $(this).addClass('active-mapstyle')
  $(this).addClass('active')
  activeLineWidth = $(this).attr('data-linewidth') / 100
  activeLineWidthStyle = activeLineWidth + '-' + activeLineStyle
  if (activeToolOption) {
    setActiveTool('line')
  }
})

function cycleLineWidth(direction) {
  var currentStep = ALLOWED_LINE_WIDTHS.indexOf(activeLineWidth * 100)
  if (direction == 1 && (currentStep == -1 || currentStep == ALLOWED_LINE_WIDTHS.length-1)) {
    currentStep = 0
  } else if (direction == -1 && currentStep <= 0) {
    currentStep = ALLOWED_LINE_WIDTHS.length-1
  } else {
    currentStep += direction
  }
  // This odd construction is because Javascript won't respect the zero after the decimal
  var button = $('button[data-linewidth="' + ALLOWED_LINE_WIDTHS[currentStep] + '"]')
  if (!button.length) {
    button = $('button[data-linewidth="' + ALLOWED_LINE_WIDTHS[currentStep] +'.0"]')
  }
  button.trigger('click')
} // cycleLineWidth()

function cycleLineStyle(direction) {
  var currentStep = ALLOWED_LINE_STYLES.indexOf(activeLineStyle)
  if (direction == 1 && (currentStep == -1 || currentStep == ALLOWED_LINE_STYLES.length-1)) {
    currentStep = 0
  } else if (direction == -1 && currentStep <= 0) {
    currentStep = ALLOWED_LINE_STYLES.length - 1
  } else {
    currentStep += direction
  }
  $('button[data-linestyle="' + ALLOWED_LINE_STYLES[currentStep] + '"]').trigger('click')
} // cycleLineStyle()

$('.line-style-choice-style').on('click', function() {
  $('.line-style-choice-style').removeClass('active')
  $('.line-style-choice-style.active-mapstyle').removeClass('active-mapstyle')
  $(this).addClass('active-mapstyle')
  $(this).addClass('active')
  activeLineStyle = $(this).attr('data-linestyle')
  activeLineWidthStyle = activeLineWidth + '-' + activeLineStyle
  if (activeToolOption) {
    setActiveTool('line')
  }

  // Hollow line buttons are two-tone and so need extra help
  var twoToneButtons = ['hollow', 'hollow_round', 'hollow_open', 'wide_stripes', 'square_stripes', 'stripes']
  var twoToneCurrent = $('#svgu_ls_' + activeLineStyle).attr('xlink:href')
  if (twoToneButtons.indexOf(activeLineStyle) > -1 && !twoToneCurrent.endsWith('-active')) {
    $('#svgu_ls_' + activeLineStyle).attr('xlink:href', twoToneCurrent + '-active')
  }
  for (var ttb of twoToneButtons) {
    var ttSVG = $('#svgu_ls_' + ttb).attr('xlink:href')
    if (activeLineStyle != ttb && ttSVG && ttSVG.endsWith('-active')) {
      $('#svgu_ls_' + ttb).attr('xlink:href', ttSVG.split('-active')[0])
    } // if was active
  } // for ttb of twoToneButtons
}) // .line-style-choice-style.click

function setLineStyle(style, ctx) {
  var pattern;
  if (ctx.globalCompositeOperation != 'source-over') {
    ctx.globalCompositeOperation = 'source-over'
  }
  if (style == 'solid') {
    pattern = []
    ctx.lineCap = 'round'
  }
  else if (style == 'dashed') {
    pattern = [gridPixelMultiplier, gridPixelMultiplier * 1.5]
    ctx.lineCap = 'square'
  }
  else if (style == 'wide_stripes') {
    pattern = [gridPixelMultiplier, gridPixelMultiplier * 2.5]
    ctx.lineCap = 'square'
  }
  else if (style == 'dotted_dense') {
    ctx.lineCap = 'butt'
    pattern = [gridPixelMultiplier / 2, gridPixelMultiplier / 4]
  }
  else if (style == 'dotted') {
    ctx.lineCap = 'butt'
    pattern = [gridPixelMultiplier / 2, gridPixelMultiplier / 2]
  }
  else if (style == 'square_stripes') {
    pattern = [gridPixelMultiplier, gridPixelMultiplier]
    ctx.lineCap = 'butt'
  }
  else if (style == 'stripes') {
    pattern = [gridPixelMultiplier, gridPixelMultiplier / 2]
    ctx.lineCap = 'butt'
  }
  else if (style == 'dense_thick') {
    pattern = [2, 2]
    ctx.lineCap = 'butt'
  }
  else if (style == 'dense_thin') {
    pattern = [1, 1]
    ctx.lineCap = 'butt'
  }
  else if (style == 'hollow_round') {
    pattern = []
    ctx.lineCap = 'round'
  }
  else if (style == 'hollow') {
    pattern = []
    ctx.lineCap = 'square'
  }
  else if (style == 'hollow_open' || style == 'color_outline') {
    pattern = []
    ctx.lineCap = 'butt'
  }
  else if (style == 'dashed_uneven') {
    pattern = [gridPixelMultiplier, gridPixelMultiplier / 5, gridPixelMultiplier / 2, gridPixelMultiplier / 5]
    ctx.lineCap = 'butt'
  }
  else if (style == 'dotted_square') {
    pattern = [ctx.lineWidth, ctx.lineWidth]
    ctx.lineCap = 'butt'
  }
  else {
    // Safety: fallback to solid
    pattern = []
    ctx.lineCap = 'round'
  }
  ctx.setLineDash(pattern)
} // setLineStyle(style, ctx)

function unfreezeMapControls() {
  // If #tool-export-canvas (screen size: xs) was clicked,
  // then the screen resized to a larger breakpoint,
  // the map controls won't be able to be unlocked.
  // Unlock them automatically, and return the map to its editable state.
  if (window.innerWidth > 768 && $('#tool-line').prop('disabled')) {
    $('#tool-export-canvas').click()
  }
  resetTooltipOrientation()
}

// Label Controls
$('#label-text, #label-shape, #label-text-color, #label-bg-color-transparent, #label-bg-color').on('change', function() {
  // Whenever any aspect of the label changes, update the map object, reset the temporaryLabel, and draw the canvas.
  var labelX = $('#label-coordinates-x').val()
  var labelY = $('#label-coordinates-y').val()

  // TOOD: Here's where I'll want to limit the character count for square and circle,
  // because it doesn't look good with too many characters crammed in

  temporaryLabel['text'] = $('#label-text').val()
  temporaryLabel['shape'] = $('#label-shape').val()
  temporaryLabel['text-color'] = $('#label-text-color').val()
  if ($('#label-bg-color-transparent').is(':checked')) {
    temporaryLabel['bg-color'] = undefined
  } else {
    temporaryLabel['bg-color'] = $('#label-bg-color').val()
  }
  activeMap = updateMapObject(labelX, labelY, false, Object.assign({}, temporaryLabel))
  autoSave(activeMap);
  temporaryLabel = {}
  drawCanvas(activeMap, true)
  drawLabelIndicator(labelX, labelY)
})

$('#tool-ruler').on('click', function() {
  rulerOn = !rulerOn
  $(this).toggleClass('remains-active')
  rulerOrigin = []
  var canvas = document.getElementById('ruler-canvas')
  var ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  if (selectedPoints.length > 0 || activeTool == 'select') {
    activeTool = 'look'
    selectedPoints = []
    clearMarchingAnts()
  }
})

function drawRuler(x, y, replaceOrigin) {
  // Displays a hover indicator on the hover canvas at x,y
  var canvas = document.getElementById('ruler-canvas')
  var ctx = canvas.getContext('2d')
  ctx.globalAlpha = 0.33
  ctx.fillStyle = '#2ECC71'
  ctx.strokeStyle = '#2ECC71'
  var gridPixelMultiplier = canvas.width / gridCols
  if (rulerOrigin.length == 0) {
    // Just draw the point
    ctx.fillRect((x - 0.5) * gridPixelMultiplier, (y - 0.5) * gridPixelMultiplier, gridPixelMultiplier, gridPixelMultiplier)
  } else if (rulerOrigin.length > 0) {
    // Calculate distance between this and origin

    // Clear the canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Re-draw the origin
    ctx.fillRect((rulerOrigin[0] - 0.5) * gridPixelMultiplier, (rulerOrigin[1] - 0.5) * gridPixelMultiplier, gridPixelMultiplier, gridPixelMultiplier)

    // Draw the new point
    ctx.fillRect((x - 0.5) * gridPixelMultiplier, (y - 0.5) * gridPixelMultiplier, gridPixelMultiplier, gridPixelMultiplier)

    // Connect the two points
    ctx.beginPath()
    ctx.lineWidth = gridPixelMultiplier
    ctx.lineCap = 'round'
    ctx.moveTo((rulerOrigin[0] * gridPixelMultiplier), (rulerOrigin[1] * gridPixelMultiplier))
    ctx.lineTo(x * gridPixelMultiplier, y * gridPixelMultiplier)
    ctx.stroke()
    ctx.closePath()

    // Draw the distance near the cursor
    ctx.textAlign = 'start'
    if (gridPixelMultiplier < preferredGridPixelMultiplier) {
      ctx.font = '700 ' + Math.max(gridPixelMultiplier, Math.floor(HIGH_QUAL_PGPM * 0.6)) + 'px sans-serif'
    } else {
      ctx.font = '700 ' + gridPixelMultiplier + 'px sans-serif'
    }
    ctx.globalAlpha = 0.67
    ctx.fillStyle = '#000000'
    var pointDistance = ''
    var deltaX = Math.abs(rulerOrigin[0] - x)
    var deltaY = Math.abs(rulerOrigin[1] - y)
    if ((!deltaX && deltaY) || (deltaX && !deltaY)) {
      // Straight line along one axis, don't need to show both
      pointDistance += (deltaX + deltaY)
    } else if (deltaX && deltaY) {
      // Show both x, y difference
      pointDistance += deltaX + ', ' + deltaY
    }
    ctx.fillText(pointDistance, (x + 1) * gridPixelMultiplier, (y + 1) * gridPixelMultiplier)
  }
  if (replaceOrigin) {
    // Don't replace the origin on hover
    rulerOrigin = [x, y]
  }
} // drawRuler(x, y, replaceOrigin)

function setActiveTool(tool, skipSaveLast) {
  if (!skipSaveLast) {
    lastToolUsed = activeTool
  }
  activeTool = tool || 'look'
  $('.active').removeClass('active')
  if (activeTool == 'line') {
    $('#tool-line').addClass('active')
    if (activeToolOption) {
      $('#tool-line').css({
        "background-color": activeToolOption,
        "color": determineDarkOrLightContrast(activeToolOption)
      })
    }
  } else if (activeTool == 'eraser') {
    $('#tool-eraser').addClass('active')
  } else if (activeTool == 'station') {
    $('#tool-station').addClass('active')
  } else if (activeTool == 'select') {
    $('#tool-select').addClass('active')
  } else if (activeTool == 'eyedropper') {
    $('#tool-eyedropper').addClass('active')
  } else if (activeTool == 'look') {
    $('#tool-look').addClass('active')
  } else if (activeTool == 'move') {
    $('#tool-move-selection').addClass('active')
  }
} // setActiveTool(tool, skipSaveLast)

$('#tool-eyedropper').on('click', function() {
  setActiveTool('eyedropper')
})

$('#tool-look').on('click', function() {
  setActiveTool('look')
})

$('#tool-select').on('click', function() {
  if (mapDataVersion < 3) { return }
  if (selectedPoints.length > 0) {
    // De-select current selection
    selectedPoints = []
    clearMarchingAnts()
    if (activeTool == 'move') {
      setActiveTool('select')
    } else if (activeTool == 'select' && lastToolUsed != 'move') {
      setActiveTool(lastToolUsed)
    }
  } else {
    setActiveTool('select')
    rulerOn = false
    rulerOrigin = []
    $('#tool-ruler').removeClass('active')
    $('#tool-ruler').removeClass('remains-active')
  }
})

function drawSelectionBox(x1, y1, x2, y2) {
  var canvas = document.getElementById('ruler-canvas') // Ruler and select can't be active at the same time, so let's borrow it
  var ctx = canvas.getContext('2d')

  // Reset to defaults so ruler doesn't take over
  ctx.fillStyle = '#000000'
  ctx.strokeStyle = '#000000'
  ctx.lineWidth = 1

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.setLineDash([4, 2])
  ctx.lineDashOffset = marchingAntsOffset

  var width = 1
  var height = 1
  var xOffset = -0.5
  var yOffset = -0.5

  if (x1 < x2) {
    width = x2 - x1
    width += 1
  } else if (x1 > x2) {
    width = (x1 - x2) * -1
    width -= 1
    xOffset *= -1
  }

  if (y1 < y2) {
    height = y2 - y1
    height += 1
  } else if (y1 > y2) {
    height = (y1 - y2) * -1
    height -= 1
    yOffset *= -1
  }

  ctx.strokeRect((x1 + xOffset) * gridPixelMultiplier, (y1 + yOffset) * gridPixelMultiplier, (width) * gridPixelMultiplier, (height) * gridPixelMultiplier)
} // drawSelectionBox(x1, y1, x2, y2)

function drawMarchingAnts(x1, y1, x2, y2) {
  marchingAntsOffset++
  if (marchingAntsOffset > 5) {
    marchingAntsOffset = 0
  }
  drawSelectionBox(x1, y1, x2, y2)
  activeMarchingAnts = setTimeout(function() {
    drawMarchingAnts(x1, y1, x2, y2)
  }, 35)
  return activeMarchingAnts
}

function clearMarchingAnts() {
  if (activeMarchingAnts) {
    clearTimeout(activeMarchingAnts)
    var canvas = document.getElementById('ruler-canvas')
    var ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)
  }
} // clearMarchingAnts()

function getPointsWithinBoundingBox(x1, y1, x2, y2) {
  // Return an array of all points within the bounding box x1, y1, x2, y2,
  //  (inclusive) in the format x, y, x, y, x, y
  var pointsWithin = []
  var startX = (x1 < x2) ? x1 : x2
  var startY = (y1 < y2) ? y1 : y2
  var endX = (x2 > x1) ? x2 : x1
  var endY = (y2 > y1) ? y2 : y1

  for (var xn=startX; xn<=endX; xn++) {
    for (var yn=startY; yn<=endY; yn++) {
      // pointsWithin.push(xn)
      // pointsWithin.push(yn)
      pointsWithin.push([xn, yn])
    }
  }

  // if (MMMDEBUG) { console.log(`pointsWithin is: ${pointsWithin}`) }
  return pointsWithin
} // getPointsWithinBoundingBox(x1, y1, x2, y2)

function isWithinSelectedPoints(x, y) {
  // For simplicity with other functions, if selectedPoints is empty,
  //  this should be trivially true (if empty, all are selected)
  if (selectedPoints.length == 0) { return true }
  var selectedPointsClone = structuredClone(selectedPoints)
  do {
    xy = selectedPointsClone.pop()
    if (x == xy[0] && y == xy[1]) {
      return true
    }
  } while (selectedPointsClone.length > 0)
  return false
} // isWithinSelectedPoints(x, y)

$('#tool-move-selection').on("click", function() {
  if (selectedPoints.length == 0) {
    return
  }
  setActiveTool('move')
})

function setMoveStationAbility(disable) {
  // By default, this should toggle,
  //  but it's useful to always disable, like when closing the station menu
  if (disable) {
    moveStationOn = []
  } else if (moveStationOn.length > 0) {
    moveStationOn = []
  } else {
    moveStationOn = [
      parseInt($('#station-coordinates-x').val()),
      parseInt($('#station-coordinates-y').val())
    ]
  }

  if (moveStationOn.length == 2) {
    $('span#move-station-enabled').text(': Arrow Keys, Mouse')
  } else {
    setTimeout(function() {
      $('#move-station').removeClass('active')
    }, 1)
    $('span#move-station-enabled').text(': Arrow Keys only')
  }
} // setMoveStationAbility(disable)

$('#move-station').on('click', function() {
  setMoveStationAbility()
})

function cycleGridStep() {
  var GRID_STEPS = [3, 5, 7, false]
  var currentStep = GRID_STEPS.indexOf(gridStep)
  if (currentStep == -1 || currentStep == GRID_STEPS.length-1) {
    gridStep = GRID_STEPS[0]
  } else {
    gridStep = GRID_STEPS[currentStep + 1]
  }
  if (!gridStep) {
    hideGrid()
  } else {
    showGrid()
  }
  window.localStorage.setItem('metroMapGridStep', gridStep);
  drawGrid()
} // cycleGridStep()

function cycleSelectMenu(select, direction) {
  if (direction == 1 && select.selectedIndex >= select.options.length - 1) {
    select.selectedIndex = 0
  } else if (direction == -1 && select.selectedIndex <= 0) {
    select.selectedIndex = select.options.length - 1
  } else {
    select.selectedIndex += direction
  }
  $(select).trigger('change')
} // cycleSelectMenu(select)

$('#tool-undo').on('click', undo)
$('#tool-redo').on('click', redo)

function restyleAllLines(toWidth, toStyle, deferSave) {
    var newMapObject = {"points_by_color": {}}
    newMapObject["stations"] = Object.assign({}, activeMap["stations"])
    newMapObject["global"] = Object.assign({}, activeMap["global"])
    for (var color in activeMap["points_by_color"]) {
      for (var lws in activeMap["points_by_color"][color]) {
        if (mapDataVersion >= 3) {
          var lw = lws.split('-')[0]
          var ls = lws.split('-')[1]
        }
        var newLws = (toWidth || lw) + '-' + (toStyle || ls)
        if (!newMapObject["points_by_color"][color]) {
          newMapObject["points_by_color"][color] = {}
        }
        if (!newMapObject["points_by_color"][color][newLws]) {
          newMapObject["points_by_color"][color][newLws] = {}
        }

        // CONSIDER: This could maybe be made more efficient?
        // Using Object.assign is ~40x faster here (0.2ms vs 8ms on a 360x fully-filled map),
        //  but I was running into intermittent issues where some line data could be lost
        //  when a given line had multiple points within the same X value, leading to Y values being dropped
        // However -- the speed difference is negligible compared to drawCanvas, so maybe not worth it
        for (var x in activeMap["points_by_color"][color][lws]) {
          for (var y in activeMap["points_by_color"][color][lws][x]) {
            if (!newMapObject["points_by_color"][color][newLws]) {
              newMapObject["points_by_color"][color][newLws] = {}
            }
            if (!newMapObject["points_by_color"][color][newLws][x]) {
              newMapObject["points_by_color"][color][newLws][x] = {}
            }
            newMapObject["points_by_color"][color][newLws][x][y] = activeMap["points_by_color"][color][lws][x][y]
          }
        }
      } // lws
    } // color
    if (mapDataVersion == 2) {
      // Upgrade from v2 to v3 is complete
      mapDataVersion = 3
      newMapObject["global"]["data_version"] = 3
      compatibilityModeIndicator()
    }
    activeMap = newMapObject
    if (!deferSave) {
      autoSave(activeMap)
      drawCanvas(activeMap)
    }
} // restyleAllLines(toWidth, toStyle, deferSave)

function upgradeMapDataVersion(desiredMapDataVersion) {
  // Upgrades to the highest mapDataVersion possible.
  if (mapDataVersion == 1) {
    if (desiredMapDataVersion && desiredMapDataVersion == 1) {
      // Hide features not yet available
      $('#line-style-options').hide()
      $('#tool-map-style, #tool-map-style-options').hide()
      $('#station-style, label[for="station-style"]').hide()
      return
    }
    var newMapObject = {
      "points_by_color": {},
      "stations": {},
    }
    newMapObject["global"] = Object.assign({}, activeMap["global"])
    var highestValue = getMapSize(activeMap) || 0
    for (allowedSize of ALLOWED_SIZES) {
      if (highestValue < allowedSize) {
        gridRows = allowedSize
        gridCols = allowedSize
        newMapObject["global"]['map_size'] = gridRows
        break
      }
    }
    newMapObject["global"]["style"] = {
      "mapLineWidth": 1,
      "mapLineStyle": 'solid'
    }
    for (var x in activeMap) {
      for (var y in activeMap[x]) {
        var color = activeMap[x][y]["line"]
        if (!color) { continue }
        if (!newMapObject["points_by_color"][color]) {
          newMapObject["points_by_color"][color] = {"xys": {}}
        }
        if (!newMapObject["points_by_color"][color]["xys"][x]) {
          newMapObject["points_by_color"][color]["xys"][x] = {}
        }
        newMapObject["points_by_color"][color]["xys"][x][y] = 1
        if (activeMap[x][y]["station"]) {
          if (!newMapObject["stations"][x]) {
            newMapObject["stations"][x] = {}
          }
          newMapObject["stations"][x][y] = Object.assign({}, activeMap[x][y]["station"])
        } // if station
      } // for y
    } // for x
    // Upgrade from v1 to v2 is complete
    mapDataVersion = 2
    newMapObject["global"]["data_version"] = 2
    activeMap = Object.assign({}, newMapObject)
  } // mapDataVersion 1
  if (mapDataVersion == 2) {
    if (desiredMapDataVersion && desiredMapDataVersion == 2) {
      // Hide features not yet available
      $('#line-style-options').hide()
      return
    }
    var toWidth = 1
    var toStyle = 'solid'
    if (activeMap["global"] && activeMap["global"]["style"] && activeMap["global"]["style"]["mapLineWidth"]) {
      toWidth = activeMap["global"]["style"]["mapLineWidth"]
    }
    if (activeMap["global"] && activeMap["global"]["style"] && activeMap["global"]["style"]["mapLineStyle"]) {
      toStyle = activeMap["global"]["style"]["mapLineStyle"]
    }
    restyleAllLines(toWidth, toStyle, true)
  }
  compatibilityModeIndicator()
  // Delete undo/redo history, because I don't want to be able to downgrade to a lower mapDataVersion by undoing
  mapHistory = []
  mapRedoHistory = []
} // upgradeMapDataVersion
