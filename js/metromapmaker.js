// MetroMapMaker.js

var gridRows = 80, gridCols = 80;

String.prototype.replaceAll = function(search, replacement) {
    var target = this;
    return target.replace(new RegExp(search, 'g'), replacement);
};

function resizeGrid(size) {
  // Change the grid size to the specified size.

  saveMapAsObject(); // Save map as we currently have it so we can load it

  // Resize the grid and paint the map on it
  gridRows = size, gridCols = size;
  loadMapFromObject(JSON.parse(window.localStorage.getItem('metroMap')));
  bindRailLineEvents();

  $('.resize-grid').removeClass('btn-primary');
  $('.resize-grid').addClass('btn-info');
  $('#tool-resize-' + size).removeClass('btn-info');
  $('#tool-resize-' + size).addClass('btn-primary');
}

function getActiveLine(x, y) {
  // Given an x, y coordinate pair, return the hex code for the line you're on.
  // Use this to retrieve the line for a given point on a map.
  try {
    var classes = document.getElementById('coord-x-' + x + '-y-' + y).className.split(/\s+/);
  } catch (e) {
    // 'With the new straight lines replacing the old bubbles system of drawing the maps onto the canvas, you will land here on occasion when the maps reach the borders. (For example, y-80 which does not exist in the 80x80 grid.) Do not panic, instead just keep on keeping on.'
    return false; 
  }
  for (var z=0; z<classes.length; z++) {
    if (classes[z].indexOf('has-line-') >= 0) {
      var activeLine = classes[z].slice(9, 15);
    }
  }
  return activeLine;
}

function getStationLines(x, y) {
  // Given an x, y coordinate pair, return the hex codes for the lines this station services.
  var classes = document.getElementById('coord-x-' + x + '-y-' + y).children[0].className.split(/\s+/);
  var stationLines = [];
  for (var z=0; z<classes.length; z++) {
    if (classes[z].indexOf('has-line-') >= 0) {
      stationLines.push(classes[z].slice(9, 15));
    }
  }
  return stationLines;
}

function bindRailLineEvents() {
  $('.rail-line').click(function() {
    if ($(this).attr('id') == 'rail-line-new') {
      // New Rail Line
      $('#tool-new-line-options').show();
    } else {
      // Existing Rail Line
      activeTool = 'line';
      activeToolOption = $(this).css('background-color');
    }
    $('#tool-station-options').hide();
    $('#tool-station').html('<i class="fa fa-map-pin" aria-hidden="true"></i> Station');
  });  
}

function drawGrid() {
  var grid = "";

  // Generate the grid
  for (var x=0; x<gridRows; x++) {
    grid += '<div class="grid-row">';
    for (var y=0; y<gridCols; y++) {
      grid += '<div id="coord-x-' + x + '-y-' + y + '" class="grid-col"></div>';
    }
    grid += '</div> <!-- div.grid-row -->';
  }

  $('#grid').html(grid);

  // Then bind events to the grid
  $('.grid-col').click(function() {

    $('#station-coordinates-x').val('');
    $('#station-coordinates-y').val('');

    if (activeTool == 'line') {
      $(this).css({
        'background-color': activeToolOption
      });
      $(this).addClass('has-line')
      $(this).addClass('has-line-' + rgb2hex(activeToolOption).slice(1, 7));
    } else if (activeTool == 'eraser') {
      $(this).css({
        'background-color': '#fff'
      });
      $(this).removeClass();
      $(this).addClass('grid-col');
      $(this).html('');
    } else if (activeTool == 'station') {

      $('#station-name').val('');
      $('#station-on-lines').html('');
      var x = $(this).attr('id').split('-').slice(2, 3);
      var y = $(this).attr('id').split('-').slice(4);
      $('#station-coordinates-x').val(x);
      $('#station-coordinates-y').val(y);
      var allLines = $('.rail-line');

      if ($(this).hasClass('has-station')) {
        // Already has a station, so clicking again shouldn't clear the existing station but should allow you to rename it and assign lines
        $('#tool-station-options').show();
        if ($(this).children().attr('id')) {
          // This station already has a name, show it in the textfield
          var stationName = $(this).children().attr('id').replaceAll('_', ' ');
          $('#station-name').val(stationName);

          // Pre-check the box if this is a transfer station
          var existingStationClasses = document.getElementById('coord-x-' + x + '-y-' + y).children[0].className.split(/\s+/);
          if (existingStationClasses.indexOf('transfer-station') >= 0) {
            $('#station-transfer').prop('checked', true);
          } else {
            $('#station-transfer').prop('checked', false);
          }

          // Select the correct orientation too.
          if (existingStationClasses.indexOf('rot135') >= 0) {
            document.getElementById('station-name-orientation').value = '135';
          } else if (existingStationClasses.indexOf('rot-45') >= 0) {
            document.getElementById('station-name-orientation').value = '-45';
          } else if (existingStationClasses.indexOf('rot45') >= 0) {
            document.getElementById('station-name-orientation').value = '45';
          } else if (existingStationClasses.indexOf('rot180') >= 0) {
            document.getElementById('station-name-orientation').value = '180';
          } else {
            document.getElementById('station-name-orientation').value = '0';
          }

          var stationOnLines = "";
          // var stationLines = getStationLines($("#station-coordinates-x").val(), $("#station-coordinates-y").val());
          var stationLines = getStationLines(x, y);
          for (var z=0; z<stationLines.length; z++) {
            if (stationLines[z]) {
              stationOnLines += "<button style='background-color: #" + stationLines[z] + "' class='station-add-lines' id='add-line-" + stationLines[z] + "'>" + $('#rail-line-' + stationLines[z]).text() + "</button>";  
            }
          }
        } else {
          // This only happens when you create a new station and then click on it again (without having named it first)
          // This fixes the bug where it would erroneously clear the station that it was sitting on and not allow you to add it back
          activeLine = getActiveLine(x, y);
          if (activeLine) {
            $(this).children().addClass('has-line-' + activeLine);
            stationOnLines = "<button style='background-color: #" + activeLine + "' class='station-add-lines' id='add-line-" + activeLine + "'>" + $('#rail-line-' + activeLine).text() + "</button>";
            stationLines = activeLine;
          }
        }
      } else {
        // Create a new station
        $(this).addClass('has-station');
        $(this).html('<div class="station"></div>');
        $('#tool-station-options').show();
        $('#station-transfer').prop('checked', false);
        var lastStationOrientation = window.localStorage.getItem('metroMapStationOrientation');
        if (lastStationOrientation) {
          document.getElementById('station-name-orientation').value = lastStationOrientation;
          $('#station-name-orientation').change(); // This way, it will be saved
        } else {
          document.getElementById('station-name-orientation').value = '0';
        }

        // Pre-populate the station with the line it sits on
        // activeLine = getActiveLine($("#station-coordinates-x").val(), $("#station-coordinates-y").val());
        activeLine = getActiveLine(x, y);
        if (activeLine) {
          // If the station is added to a space with no rail line, don't add any active lines
          $(this).children().addClass('has-line-' + activeLine);
          stationOnLines = "<button style='background-color: #" + activeLine + "' class='station-add-lines' id='add-line-" + activeLine + "'>" + $('#rail-line-' + activeLine).text() + "</button>";
          stationLines = activeLine;

          // Pre-populate the station with its neighboring lines
          for (var nx=-1; nx<=1; nx+=1) {
            for (var ny=-1; ny<=1; ny+=1) {
              neighboringLine = getActiveLine(parseInt(x) + parseInt(nx), parseInt(y) + parseInt(ny));  
              if (neighboringLine) {
                $(this).children().addClass('has-line-' + neighboringLine);
                if (typeof stationLines == "string") {
                  stationLines = [stationLines]
                }
                if (stationOnLines && stationOnLines.indexOf(neighboringLine) >= 0) {
                  // Don't add lines that are already added
                } else {
                  stationOnLines += "<button style='background-color: #" + neighboringLine + "' class='station-add-lines' id='add-line-" + neighboringLine + "'>" + $('#rail-line-' + neighboringLine).text() + "</button>";
                  stationLines.push(neighboringLine);
                }
              } // if (neighboringLine)
            } // for ny
          } // for nx
        } // if (activeLine)
        
      }

      // Make the station options button collapsible
      if ($('#tool-station-options').is(':visible')) {
        $('#tool-station').html('<i class="fa fa-map-pin" aria-hidden="true"></i> Hide Station Options');
      }

      // Add lines to the "Other lines this station serves" option
      if (stationOnLines) {
        $('#station-on-lines').html(stationOnLines);

        var linesToAdd = "";
        
        for (var z=0; z<allLines.length; z++) {
          if ((stationLines == allLines[z].id.slice(10, 16) || stationLines.indexOf(allLines[z].id.slice(10,16)) >= 0) || allLines[z].id.slice(10,16) == 'new') {
            // Looping through all of the lines, if this line is already in the station's lines, don't add it
            // Don't add the "Add new line" button either
          } else {
            linesToAdd += '<button style="background-color: #' + allLines[z].id.slice(10, 16) + '" class="station-add-lines" id="add-line-' + allLines[z].id.slice(10, 16) + '">' + $('#' + allLines[z].id).text() + '</button>';
          }
        } // for allLines
        if (linesToAdd) {
          $('#station-other-lines').html(linesToAdd);
          // Bind the event to the .station-add-lines buttons here since they are newly created.
          $('.station-add-lines').click(function() {
            if ($(this).parent().attr('id') == 'station-other-lines') {
              $('#station-on-lines').append($(this));
              $('#coord-x-' + x + '-y-' + y).children().addClass('has-line-' + $(this).attr('id').slice(9, 15));

            } else {
              // Remove it
              $('#station-other-lines').append($(this));
              $('#coord-x-' + x + '-y-' + y).children().removeClass('has-line-' + $(this).attr('id').slice(9, 15));
            }
            
          });
        } // if linesToAdd
      } // if stationOnLines

      // Indicate which station is currently selected
      // First, remove all existing selections
      $('.active').removeClass('active');
      // Then add the active class
      $(this).children().addClass('active');

      $('#station-name').focus(); // Set focus to the station name box to save you a click each time
    } // if activeTool == station
  });

  $('.grid-col').mouseover(function() {
    if (mouseIsDown) {
      $(this).click();
      saveMapAsObject();
    }
  });

}

function rgb2hex(rgb) {
    if (/^#[0-9A-F]{6}$/i.test(rgb)) return rgb;

    rgb = rgb.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
    function hex(x) {
        return ("0" + parseInt(x).toString(16)).slice(-2);
    }
    return "#" + hex(rgb[1]) + hex(rgb[2]) + hex(rgb[3]);
}

function autoSave() {
  // TODO
}

function getURLParameter(name) {
    return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search) || [null, ''])[1].replace(/\+/g, '%20')) || null;
}

function autoLoad() {
  var savedMapHash = getURLParameter('map');
  if (savedMapHash) {
    $.get('https://metromapmaker.com/save/' + savedMapHash).done(function (savedMapData) {
      savedMapData = savedMapData.replaceAll('u&#39;', '"').replaceAll('&#39;', '"');
      getMapSize(savedMapData);
      loadMapFromObject(JSON.parse(savedMapData));
    });
  } else if (window.localStorage.getItem('metroMap')) {
    // Load from local storage
    metroMapObject = JSON.parse(window.localStorage.getItem('metroMap'));
    getMapSize(metroMapObject);
    loadMapFromObject(metroMapObject);
  } else {
    // If no map URLParameter and no locally stored map, default to the WMATA map
    // I think this would be more intuitive than the blank slate,
    //    and might limit the number of blank / red-squiggle maps created.
    // If the WMATA map ever changes, I'll need to update it here too.
    $.get('https://metromapmaker.com/save/1G_CzWEg').done(function (savedMapData) {
      savedMapData = savedMapData.replaceAll('u&#39;', '"').replaceAll('&#39;', '"');
      getMapSize(savedMapData);
      loadMapFromObject(JSON.parse(savedMapData));
    });
  }
  $('#tool-resize-' + gridRows).text('Initial size (' + gridRows + 'x' + gridCols + ')');
}

function getMapSize(metroMapObject) {
    highestValue = 0;
    if (typeof metroMapObject !== 'object') {
      metroMapObject = JSON.parse(metroMapObject);
    }
    for (var x in metroMapObject) {
        if (metroMapObject.hasOwnProperty(x)) {
          if (parseInt(x) > highestValue) {
            highestValue = parseInt(x);
          }
          for (var y in metroMapObject[x]) {
            if (metroMapObject[x].hasOwnProperty(y)) {
              if (parseInt(y) > highestValue) {
                highestValue = parseInt(y);
              }
            }
          } // for var y
        } // if has x
      } // for var x

    if (highestValue >= 120) {
      gridRows = 160, gridCols = 160;
    } else if (highestValue >= 80) {
      gridRows = 120, gridCols = 120;
    } else {
      gridRows = 80, gridCols = 80;
    }
} // getMapSize()

function loadMapFromObject(metroMapObject) {

  drawGrid();

  for (var x in metroMapObject) {
    if (metroMapObject.hasOwnProperty(x)) {
      for (var y in metroMapObject[x]) {
        if (metroMapObject[x].hasOwnProperty(y)) {
          $('#coord-x-' + x + '-y-' + y).addClass('has-line');
          $('#coord-x-' + x + '-y-' + y).addClass('has-line-' + metroMapObject[x][y]['line']);
          $('#coord-x-' + x + '-y-' + y).css({
              'background-color': '#' + metroMapObject[x][y]['line']
          });
          if (metroMapObject[x][y]["station"]) {
            $('#coord-x-' + x + '-y-' + y).addClass('has-station');
            $('#coord-x-' + x + '-y-' + y).attr('data-toggle', 'tooltip');
            $('#coord-x-' + x + '-y-' + y).attr('title', metroMapObject[x][y]["station"]["name"]);
            $('#coord-x-' + x + '-y-' + y).html('<div id="' + metroMapObject[x][y]["station"]["name"] +'" class="station"></div>');
            if (metroMapObject[x][y]["station"]["transfer"] == 1) {
              $('#' + metroMapObject[x][y]["station"]["name"]).addClass('transfer-station');
            }
            if (metroMapObject[x][y]["station"]["lines"] && metroMapObject[x][y]['station']['name']) {
              for (var z=0; z<metroMapObject[x][y]["station"]["lines"].length; z++) {
                $('#' + metroMapObject[x][y]["station"]["name"]).addClass('has-line-' + metroMapObject[x][y]["station"]["lines"][z]);
                // Rail line buttons should use their color for the buttons, too.
                $('<style>').prop('type', 'text/css')
                .html('#rail-line-' + metroMapObject[x][y]["station"]["lines"][z] + ', .has-line-' + metroMapObject[x][y]["station"]["lines"][z] + '{ background-color: #' + metroMapObject[x][y]["station"]["lines"][z] + '; }').appendTo('head');
              } // for lines
              if (metroMapObject[x][y]["station"]["orientation"] == '180') {
                $('#' + metroMapObject[x][y]["station"]["name"]).addClass('rot180');
              } else if (metroMapObject[x][y]["station"]["orientation"] == '-45') {
                $('#' + metroMapObject[x][y]["station"]["name"]).addClass('rot-45');
              } else if (metroMapObject[x][y]["station"]["orientation"] == '45') {
                $('#' + metroMapObject[x][y]["station"]["name"]).addClass('rot45');
              } else if (metroMapObject[x][y]["station"]["orientation"] == '135') {
                $('#' + metroMapObject[x][y]["station"]["name"]).addClass('rot135');
              } // if station orientation
            } // if station name, lines
          } // if station
        } // if y
      } // for y in x
    } // if x
  } // for x in map

  if (Object.keys(metroMapObject['global']['lines']).length > 0) {
    // Remove original rail lines if the map has its own preset rail lines
    $('#tool-line-options button.original-rail-line').remove();
  }

  for (var line in metroMapObject['global']['lines']) {
    if (metroMapObject['global']['lines'].hasOwnProperty(line) && document.getElementById('rail-line-' + line) === null) {
        $('#rail-line-new').before('<button id="rail-line-' + line + '" class="rail-line btn-info" style="background-color: #' + line + ';">' + metroMapObject['global']['lines'][line]['displayName'] + '</button>');
    }
  }

  $(function () {
    $('[data-toggle="tooltip"]').tooltip();
    bindRailLineEvents();
  }); // Do this here because it looks like the call to this below doesn't happen in time to load all the tooltips created by the map being loaded
} // function loadMapFromObject

function saveMapAsObject() {
  console.log('Saving');

  metroMap = new Object;

  for (var x=0; x<gridRows; x++) {
    for (var y=0; y<gridCols; y++) {
      var classes = document.getElementById('coord-x-' + x + '-y-' + y).className.split(/\s+/);

      // Example: ["grid-col", "has-line", "has-line-f0ce15", "has-station"]
      if (classes.indexOf('has-line') >= 0) {
        if (metroMap[x] === undefined) {
          metroMap[x] = new Object;
        }
        if (metroMap[x][y] === undefined) {
          metroMap[x][y] = new Object;
        }

        activeLine = getActiveLine(x, y);
        metroMap[x][y]['line'] = activeLine;

        // Stations must exist on a line in order to be valid.
        if (classes.indexOf('has-station') >= 0) {
          var stationLines = getStationLines(x, y);
          var activeStation = document.getElementById('coord-x-' + x + '-y-' + y).children[0].id;
          if (activeStation) {
            // Stations must have a name in order to be valid.
              metroMap[x][y]['station'] = {
              'name': activeStation,
              'lines': stationLines
            }
            if ($('#' + activeStation).hasClass('transfer-station')) {
              metroMap[x][y]['station']['transfer'] = 1;
            } // if transfer station
            if ($('#' + activeStation).hasClass('rot180')) {
              metroMap[x][y]['station']['orientation'] = '180';
            } else if ($('#' + activeStation).hasClass('rot-45')) {
              metroMap[x][y]['station']['orientation'] = '-45';
            } else if ($('#' + activeStation).hasClass('rot45')) {
              metroMap[x][y]['station']['orientation'] = '45';
            } else if ($('#' + activeStation).hasClass('rot135')) {
              metroMap[x][y]['station']['orientation'] = '135';
            } else {
              metroMap[x][y]['station']['orientation'] = '0';
            }
          } // if station name
        } // if has-station
      } // if has-line
    } // for y
  } // for x

  // Save the names of the rail lines
  metroMap['global'] = new Object;
  metroMap['global']['lines'] = new Object;
  $('.rail-line').each(function() {
    if ($(this).attr('id') != 'rail-line-new') {
      // rail-line-
      metroMap['global']['lines'][$(this).attr('id').slice(10, 16)] = {
        'displayName': $(this).text()
      }
    }
  });

  window.localStorage.setItem('metroMap', JSON.stringify(metroMap));

  $('#autosave-indicator').html('<i class="fa fa-spinner fa-spin" aria-hidden="true"></i> Saving ...')
  setTimeout(function() {
    $('#autosave-indicator').html('');
  }, 1500)

  return JSON.stringify(metroMap);
} // function saveMapAsObject()

$(document).ready(function() {

  // Bind to the mousedown and mouseup events so we can implement dragging easily
  mouseIsDown = false;
  $(document).mousedown(function() {
      mouseIsDown = true;
  }).mouseup(function() {
      mouseIsDown = false;
  });

  drawGrid();
  autoLoad();
  bindRailLineEvents();
  
  $('.start-hidden').each(function() {
    $(this).hide();
  })

  // Enable the tooltips
  $(function () {
    $('[data-toggle="tooltip"]').tooltip();
  })

  activeTool = 'look';

  $('#toolbox button').click(function() {
    $('#toolbox button').removeClass('btn-primary').addClass('btn-info');
    $(this).removeClass('btn-info');
    $(this).addClass('btn-primary')
  })

  // Toolbox
  $('#tool-line').click(function() {
    // Expand Rail line options
    if ($('#tool-line-options').is(':visible')) {
      $('#tool-line-options').hide();
      $('#tool-new-line-options').hide();
      $('#tool-line').html('<i class="fa fa-subway" aria-hidden="true"></i> Rail Line');
    } else {
      $('#tool-line-options').show();
      $('#tool-line').html('<i class="fa fa-subway" aria-hidden="true"></i> Hide Rail Line options');
    }
    $('.tooltip').hide();
  });
  $('#rail-line-delete').click(function() {
    // Only delete lines that aren't in use
    var allLines = $('.rail-line');
    var linesToDelete = [];
    for (var a=0; a<allLines.length; a++) {
      if ($('.rail-line')[a].id != 'rail-line-new') {
        // Is this line in use at all?
        if ($('.has-line-' + $('.rail-line')[a].id.slice(10, 16)).length == 0) {
          linesToDelete.push($('#' + $('.rail-line')[a].id));
        }
      }
    }
    if (linesToDelete.length > 0) {
      for (var d=0; d<linesToDelete.length; d++) {
        linesToDelete[d].remove();
      }
    }
  });
  $('#tool-station').click(function() {
    activeTool = 'station';
    if ($('#tool-station-options').is(':visible')) {
      $('#tool-station-options').hide();
      $('#tool-station').html('<i class="fa fa-map-pin" aria-hidden="true"></i> Station');
    }
    $('.tooltip').hide();
  });
  $('#tool-eraser').click(function() {
    activeTool = 'eraser';
    $('#tool-station-options').hide();
    $('#tool-station').html('<i class="fa fa-map-pin" aria-hidden="true"></i> Station');
    $('.tooltip').hide();
  })
  $('#tool-look').click(function() {
    activeTool = 'look';
  });
  $('#tool-grid').click(function() {
    if ($('.grid-col').css('border-color') == 'rgb(128, 206, 255)' || $('.grid-col').css('border-top-color') == 'rgb(128, 206, 255)') {
      $('.grid-col').css('border-color', '#fff');
      $('#tool-grid').html('<i class="fa fa-table" aria-hidden="true"></i> Show grid');
    } else {
      $('.grid-col').css('border-color', '#80CEFF');
      $('#tool-grid').html('<i class="fa fa-table" aria-hidden="true"></i> Hide grid');
    }
  });
  $('#tool-zoom-in').click(function() {
    var gridSize = $('.grid-col').width();
    if (gridSize < 50) {
      $('.grid-col').width(gridSize + 2);
      $('.grid-col').height(gridSize + 2);
    }
  });
  $('#tool-zoom-out').click(function() {
    var gridSize = $('.grid-col').width();
    if (gridSize > 8) {
      $('.grid-col').width(gridSize - 2);
      $('.grid-col').height(gridSize - 2); 
    }
  });
  $('#tool-resize-all').click(function() {
    if ($('#tool-resize-options').is(':visible')) {
      $('#tool-resize-options').hide();
      $('#tool-resize-all').html('<i class="fa fa-expand" aria-hidden="true"></i> Resize grid');
    } else {
      $('#tool-resize-options').show();
      $('#tool-resize-all').html('<i class="fa fa-expand" aria-hidden="true"></i> Hide Resize options');
    }
    $('.tooltip').hide();
  });
  $('.resize-grid').click(function() {
    size = $(this).attr('id').split('-').slice(2);
    resizeGrid(size);
  })
  $('#tool-move-all').click(function() {
    if ($('#tool-move-options').is(':visible')) {
      $('#tool-move-options').hide();
      $('#tool-move-all').html('<i class="fa fa-arrows" aria-hidden="true"></i> Move map')
    } else {
      $('#tool-move-options').show();
      $('#tool-move-all').html('<i class="fa fa-arrows" aria-hidden="true"></i> Hide Move options')
    }
    $('.tooltip').hide();
  });
  $('#tool-move-up').click(function() {
    // If the grid has been zoomed in or out, preserve that sizing
    var gridSize = $('.grid-col').width();

    for (var y=0; y<gridCols; y++) {
      for (var x=0; x<gridRows; x++) {

        // Remove all classes from current grid item (except .grid-col)
        var classes = document.getElementById('coord-x-' + x + '-y-' + y).className.split(/\s+/);
        for (var c=0; c<classes.length; c++) {
          if (classes[c] != 'grid-col') {
            // Don't remove .grid-col or you'll have to re-bind all of the .grid-col events
            $('#coord-x-' + x + '-y-' + y).removeClass(classes[c]);
          }
        }

        if (y == gridRows - 1) {
          // Clear the last row
          $('#coord-x-' + x + '-y-' + y).html('');
          $('#coord-x-' + x + '-y-' + y).removeAttr('style');
        } else {
          // Get all classes from the next grid item
          var classes = document.getElementById('coord-x-' + x + '-y-' + parseInt(y + 1)).className.split(/\s+/);

          // Move all classes from the next grid item to the current
          for (var c=0; c<classes.length; c++) {
            // Move all classes
            if (classes[c] != 'grid-col') {
              $('#coord-x-' + x + '-y-' + y).addClass(classes[c]);
            }
            // Move all styling
            $('#coord-x-' + x + '-y-' + y).removeAttr('style');
            $('#coord-x-' + x + '-y-' + y).attr('style', $('#coord-x-' + x + '-y-' + parseInt(y + 1)).attr('style'));
          }

          // Move any children too, overwriting any existing contents
          $('#coord-x-' + x + '-y-' + y).html($('#coord-x-' + x + '-y-' + parseInt(y + 1)).html());
        }
      } // for x
    } // for y
    $('.grid-col').width(gridSize);
    $('.grid-col').height(gridSize);
  });
  $('#tool-move-down').click(function() {
    // If the grid has been zoomed in or out, preserve that sizing
    var gridSize = $('.grid-col').width();

    for (var y=gridCols - 1; y>=0; y--) {
      for (var x=0; x<gridRows; x++) {

        // Remove all classes from current grid item (except .grid-col)
        var classes = document.getElementById('coord-x-' + x + '-y-' + y).className.split(/\s+/);
        for (var c=0; c<classes.length; c++) {
          if (classes[c] != 'grid-col') {
            // Don't remove .grid-col or you'll have to re-bind all of the .grid-col events
            $('#coord-x-' + x + '-y-' + y).removeClass(classes[c]);
          }
        }

        if (y == 0) {
          // Clear the last row
          $('#coord-x-' + x + '-y-' + y).html('');
          $('#coord-x-' + x + '-y-' + y).removeAttr('style');
        } else {
          // Get all classes from the next grid item
          var classes = document.getElementById('coord-x-' + x + '-y-' + parseInt(y - 1)).className.split(/\s+/);

          // Move all classes from the next grid item to the current
          for (var c=0; c<classes.length; c++) {
            // Move all classes
            if (classes[c] != 'grid-col') {
              $('#coord-x-' + x + '-y-' + y).addClass(classes[c]);
            }
            // Move all styling
            $('#coord-x-' + x + '-y-' + y).removeAttr('style');
            $('#coord-x-' + x + '-y-' + y).attr('style', $('#coord-x-' + x + '-y-' + parseInt(y - 1)).attr('style'));
          }

          // Move any children too, overwriting any existing contents
          $('#coord-x-' + x + '-y-' + y).html($('#coord-x-' + x + '-y-' + parseInt(y - 1)).html());
        }
      } // for x
    } // for y
    $('.grid-col').width(gridSize);
    $('.grid-col').height(gridSize);
  });
  $('#tool-move-left').click(function() {
    // If the grid has been zoomed in or out, preserve that sizing
    var gridSize = $('.grid-col').width();

    for (var x=0; x<gridRows; x++) {
      for (var y=0; y<gridCols; y++) {

        // Remove all classes from current grid item (except .grid-col)
        var classes = document.getElementById('coord-x-' + x + '-y-' + y).className.split(/\s+/);
        for (var c=0; c<classes.length; c++) {
          if (classes[c] != 'grid-col') {
            // Don't remove .grid-col or you'll have to re-bind all of the .grid-col events
            $('#coord-x-' + x + '-y-' + y).removeClass(classes[c]);
          }
        }

        if (x == gridCols -1) {
          // Clear the last column
          $('#coord-x-' + x + '-y-' + y).html('');
          $('#coord-x-' + x + '-y-' + y).removeAttr('style');
        } else {
          // Get all classes from the next grid item
          var classes = document.getElementById('coord-x-' + parseInt(x + 1) + '-y-' + y).className.split(/\s+/);

          // Move all classes from the next grid item to the current
          for (var c=0; c<classes.length; c++) {
            // Move all classes
            if (classes[c] != 'grid-col') {
              $('#coord-x-' + x + '-y-' + y).addClass(classes[c]);
            }
            // Move all styling
            $('#coord-x-' + x + '-y-' + y).removeAttr('style');
            $('#coord-x-' + x + '-y-' + y).attr('style', $('#coord-x-' + parseInt(x + 1) + '-y-' + y).attr('style'));
          }

          // Move any children too, overwriting any existing contents
          $('#coord-x-' + x + '-y-' + y).html($('#coord-x-' + parseInt(x + 1) + '-y-' + y).html());
        }
      } // for y
    } // for x
    $('.grid-col').width(gridSize);
    $('.grid-col').height(gridSize);
  });
  $('#tool-move-right').click(function() {
    // If the grid has been zoomed in or out, preserve that sizing
    var gridSize = $('.grid-col').width();

    for (var x=gridRows - 1; x>=0; x--) {
      for (var y=0; y<gridCols; y++) {

        // Remove all classes from current grid item (except .grid-col)
        var classes = document.getElementById('coord-x-' + x + '-y-' + y).className.split(/\s+/);
        for (var c=0; c<classes.length; c++) {
          if (classes[c] != 'grid-col') {
            // Don't remove .grid-col or you'll have to re-bind all of the .grid-col events
            $('#coord-x-' + x + '-y-' + y).removeClass(classes[c]);
          }
        }

        if (x == 0) {
          // Clear the last column
          $('#coord-x-' + x + '-y-' + y).html('');
          $('#coord-x-' + x + '-y-' + y).removeAttr('style');
        } else {
          // Get all classes from the next grid item
          var classes = document.getElementById('coord-x-' + parseInt(x - 1) + '-y-' + y).className.split(/\s+/);

          // Move all classes from the next grid item to the current
          for (var c=0; c<classes.length; c++) {
            // Move all classes
            if (classes[c] != 'grid-col') {
              $('#coord-x-' + x + '-y-' + y).addClass(classes[c]);
            }
            // Move all styling
            $('#coord-x-' + x + '-y-' + y).removeAttr('style');
            $('#coord-x-' + x + '-y-' + y).attr('style', $('#coord-x-' + parseInt(x - 1) + '-y-' + y).attr('style'));
          }

          // Move any children too, overwriting any existing contents
          $('#coord-x-' + x + '-y-' + y).html($('#coord-x-' + parseInt(x - 1) + '-y-' + y).html());
        }
      } // for y
    } // for x
    $('.grid-col').width(gridSize);
    $('.grid-col').height(gridSize);
  });
  $('#tool-save-map').click(function() {
    activeTool = 'look';
    var savedMap = saveMapAsObject();
    var saveMapURL = 'https://metromapmaker.com/save/';
    $.post( saveMapURL, {
      'metroMap': savedMap
    }).done(function(data) {
      if (data.slice(0,7) == '[ERROR]') {

      } else {
        $('#tool-save-options').html('<h5 style="overflow-x: hidden;">Map Saved! You can share your map with a friend by using this link: <a id="shareable-map-link" href="https://metromapmaker.com/?map=' + data.replace(/\s/g,'') + ' " target="_blank">https://metromapmaker.com/?map=' + data.replace(/\s/g,'') + '</a></h5> <h5>You can then share this URL with a friend - and they can remix your map without you losing your original! If you make changes to this map, click Save and Share again to get a new URL.</h5>');
        $('#tool-save-options').show();
      }
    });
    $('.tooltip').hide();
  });
  $('#tool-export-canvas').click(function() {
    activeTool = 'look';
    $('#tool-station-options').hide();
    $('#tool-station').html('<i class="fa fa-map-pin" aria-hidden="true"></i> Station');

    $('.tooltip').hide();
    if ($('#grid').is(':visible')) {
      $('#grid').hide();
      $('#canvas-container').show();
      $('#export-canvas-help').show();
      $('button').attr('disabled', true);
      $(this).attr('disabled', false);
      $('#tool-export-canvas').html('<i class="fa fa-pencil-square-o" aria-hidden="true"></i> Edit map');
      $(this).attr('title', "Go back to editing your map").tooltip('fixTitle').tooltip('show');
    } else {
      $('#grid').show();
      $('#canvas-container').hide();
      $('#export-canvas-help').hide();
      $('button').attr('disabled', false);
      $('#tool-export-canvas').html('<i class="fa fa-file-image-o" aria-hidden="true"></i> Download as image');
      $(this).attr('title', "See what your finished map looks like").tooltip('fixTitle').tooltip('show');
    }
    // Hide the changed tooltip after a moment
    setTimeout(function() {
      $('.tooltip').hide();
    }, 1500);
    
    var canvas = document.getElementById('metro-map-canvas');
    var ctx = canvas.getContext('2d');

    // How much larger is the canvas than the grid has in squares?
    // If the grid has 80x80 squares and the canvas is 1600x1600,
    //    then the gridPixelMultiplier is 20 (1600 / 80)
    var gridPixelMultiplier = canvas.width / gridCols; // 20

    // Clear the old canvas if it was drawn
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Make the background white instead of transparent
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (var x=0; x<gridRows; x++){
      for (var y=0; y<gridCols; y++) {

        if ($('#coord-x-' + x + '-y-' + y).hasClass('has-line')) {
          // Get color of the line
          ctx.fillStyle = '#' + getActiveLine(x, y);

          ctx.beginPath();
          ctx.strokeStyle = '#' + getActiveLine(x, y);
          ctx.lineWidth = gridPixelMultiplier * 1.75;

          if (getActiveLine(x, y) == getActiveLine(x + 1, y + 1)) {
            // Direction: SE
            ctx.moveTo(x * gridPixelMultiplier, y * gridPixelMultiplier);
            ctx.lineTo((x + 1) * gridPixelMultiplier, (y + 1) * gridPixelMultiplier);
            ctx.stroke();
          } else if (getActiveLine(x, y) == getActiveLine(x + 1, y - 1)) {
            // Direction: NE
            ctx.moveTo(x * gridPixelMultiplier, y * gridPixelMultiplier);
            ctx.lineTo((x + 1) * gridPixelMultiplier, (y - 1) * gridPixelMultiplier);
            ctx.stroke();
          } else if (getActiveLine(x, y) == getActiveLine(x + 1, y)) {
            // Direction: E
            ctx.moveTo(x * gridPixelMultiplier, y * gridPixelMultiplier);
            ctx.lineTo((x + 1.5) * gridPixelMultiplier, y * gridPixelMultiplier);
            ctx.stroke();
          } else if (getActiveLine(x, y) == getActiveLine(x, y + 1)) {
            // Direction: S
            ctx.moveTo(x * gridPixelMultiplier, y * gridPixelMultiplier);
            ctx.lineTo(x * gridPixelMultiplier, (y + 1.5) * gridPixelMultiplier);
            ctx.stroke();
          }

          // Always: draw a circle, to smooth out the edges
          // arc(x, y, radius, startAngle, endAngle, anticlockwise)
          // Draw an arc centered at x, y position with radius r
          ctx.arc(x * gridPixelMultiplier, y * gridPixelMultiplier, gridPixelMultiplier * .9, 0, Math.PI * 2, true); // Rail-line circle
          ctx.closePath();
          ctx.fill();
        } // if .has-line
      } // for y
    } // for x

    // Draw the stations last (and separately), or they will be painted over by the lines themselves.
    ctx.font = '700 20px sans-serif';

    for (var x=0; x<gridRows; x++){
      for (var y=0; y<gridCols; y++) {
        if ($('#coord-x-' + x + '-y-' + y).hasClass('has-station') && $('#coord-x-' + x + '-y-' + y).children().hasClass('transfer-station')) {
          // Outer circle
          ctx.fillStyle = '#000000';
          ctx.beginPath();
          ctx.arc(x * gridPixelMultiplier, y * gridPixelMultiplier, gridPixelMultiplier * 1.2, 0, Math.PI * 2, true); 
          ctx.closePath();
          ctx.fill();

          // Inner circle
          ctx.fillStyle = '#ffffff';
          ctx.beginPath();
          ctx.arc(x * gridPixelMultiplier, y * gridPixelMultiplier, gridPixelMultiplier * .9, 0, Math.PI * 2, true); 
          ctx.closePath();
          ctx.fill();

          // Outer circle
          ctx.fillStyle = '#000000';
          ctx.beginPath();
          ctx.arc(x * gridPixelMultiplier, y * gridPixelMultiplier, gridPixelMultiplier * .6, 0, Math.PI * 2, true); 
          ctx.closePath();
          ctx.fill();

          // Inner circle
          ctx.fillStyle = '#ffffff';
          ctx.beginPath();
          ctx.arc(x * gridPixelMultiplier, y * gridPixelMultiplier, gridPixelMultiplier * .3, 0, Math.PI * 2, true); 
          ctx.closePath();
          ctx.fill();

          
        } else if ($('#coord-x-' + x + '-y-' + y).hasClass('has-station')) {
          // Outer circle
          ctx.fillStyle = '#000000';
          ctx.beginPath();
          ctx.arc(x * gridPixelMultiplier, y * gridPixelMultiplier, gridPixelMultiplier * .6, 0, Math.PI * 2, true); 
          ctx.closePath();
          ctx.fill();

          // Inner circle
          ctx.fillStyle = '#ffffff';
          ctx.beginPath();
          ctx.arc(x * gridPixelMultiplier, y * gridPixelMultiplier, gridPixelMultiplier * .3, 0, Math.PI * 2, true); 
          ctx.closePath();
          ctx.fill();
        } // if .has-station

        // Write the station name
        if ($('#coord-x-' + x + '-y-' + y).hasClass('has-station')) {
          ctx.save();
          ctx.fillStyle = '#000000';
          var activeStation = document.getElementById('coord-x-' + x + '-y-' + y).children[0].id.replaceAll('_', ' ');

          // Rotate the canvas if specified in the station name orientation
          if ($('#coord-x-' + x + '-y-' + y + ' .station').hasClass('rot-45')) {
            ctx.translate(x * gridPixelMultiplier, y * gridPixelMultiplier);  
            ctx.rotate(-45 * (Math.PI/ 180));
            if ($('#coord-x-' + x + '-y-' + y).children().hasClass('transfer-station')) {
              ctx.fillText(activeStation, 30, 5);
            } else {
              ctx.fillText(activeStation, 15, 5);
            }
          } else if ($('#coord-x-' + x + '-y-' + y + ' .station').hasClass('rot45')) {
            ctx.translate(x * gridPixelMultiplier, y * gridPixelMultiplier);
            ctx.rotate(45 * (Math.PI/ 180));
            if ($('#coord-x-' + x + '-y-' + y).children().hasClass('transfer-station')) {
              ctx.fillText(activeStation, 30, 5);
            } else {
              ctx.fillText(activeStation, 15, 5);
            }
          } else if ($('#coord-x-' + x + '-y-' + y + ' .station').hasClass('rot135')) {
            var textSize = ctx.measureText(activeStation).width;
            ctx.translate(x * gridPixelMultiplier, y * gridPixelMultiplier);
            ctx.rotate(-45 * (Math.PI/ 180));
            if ($('#coord-x-' + x + '-y-' + y).children().hasClass('transfer-station')) {
              ctx.fillText(activeStation, -1 * textSize - 30, 5);
            } else {
              ctx.fillText(activeStation, -1 * textSize - 15, 5);
            }
          } else if ($('#coord-x-' + x + '-y-' + y + ' .station').hasClass('rot180')) {
            // When drawing on the left, this isn't very different from drawing on the right 
            //      with no rotation, except that we measure the text first
            var textSize = ctx.measureText(activeStation).width;
            if ($('#coord-x-' + x + '-y-' + y).children().hasClass('transfer-station')) {
              ctx.fillText(activeStation, (x * gridPixelMultiplier) - (gridPixelMultiplier * 1.5) - textSize, (y * gridPixelMultiplier) + gridPixelMultiplier / 4);
            } else {
              ctx.fillText(activeStation, (x * gridPixelMultiplier) - (gridPixelMultiplier) - textSize, (y * gridPixelMultiplier) + gridPixelMultiplier / 4);
            }
          } else  {
            if ($('#coord-x-' + x + '-y-' + y).children().hasClass('transfer-station')) {
              ctx.fillText(activeStation, (x * gridPixelMultiplier) + (gridPixelMultiplier * 1.5), (y * gridPixelMultiplier) + gridPixelMultiplier / 4);
            } else {
              ctx.fillText(activeStation, (x * gridPixelMultiplier) + gridPixelMultiplier, (y * gridPixelMultiplier) + gridPixelMultiplier / 4);
            }  
          } // else (of if station hasClass .rot-45)

          ctx.restore();
        } // if .has-station (to write the station name)
      } // for y
    } // for x

    // Has a shareable link been created for this map? If so, add it to the corner
    if ($('#shareable-map-link').length) {
      ctx.font = '700 20px serif';
      ctx.fillStyle = '#000000';
      var shareableLink = $('#shareable-map-link').text();
      if (shareableLink.length > 0 && shareableLink.slice(0, 26) == "https://metromapmaker.com/") {
        var remixCredit = 'Remix this map! Go to ' + shareableLink;
        var textWidth = ctx.measureText(remixCredit).width;
        ctx.fillText(remixCredit, (gridRows * gridPixelMultiplier) - textWidth, (gridCols * gridPixelMultiplier) - 25);
      }
    }

    // Add a map credit to help promote the site
    ctx.font = '700 20px sans-serif';
    ctx.fillStyle = '#000000';
    var mapCredit = 'Created with MetroMapMaker.com';
    var textWidth = ctx.measureText(mapCredit).width;
    ctx.fillText(mapCredit, (gridRows * gridPixelMultiplier) - textWidth, (gridCols * gridPixelMultiplier) - 50);

  }); // #tool-export-canvas.click()
  $('#tool-clear-map').click(function() {
    drawGrid();
    $('.tooltip').hide();
  });

  $('#create-new-rail-line').click(function() {

    $('#new-rail-line-name').val($('#new-rail-line-name').val().replaceAll('<', '').replaceAll('>', '').replaceAll('"', '').replaceAll('&', '&amp;').replaceAll('/', '&#x2f;').replaceAll("'", '&#27;'));

    var allColors = [], allNames = [];
    $('.rail-line').each(function() {
      allColors.push($(this).attr('id').slice(10, 16));
      allNames.push($(this).text());
    });

    if (allColors.indexOf($('#new-rail-line-color').val().slice(1, 7)) >= 0) {
      // This color already exists!
      $('#tool-new-line-errors').text('This color already exists! Please choose a new color.');
    } else if (allNames.indexOf($('#new-rail-line-name').val()) >= 0) {
      // This rail name already exists!
      $('#tool-new-line-errors').text('This rail line name already exists! Please choose a new name.');
    } else if ($('#new-rail-line-name').val().length == 0) {
      $('#tool-new-line-errors').text('This rail line name cannot be blank. Please enter a name.');
    } else {
      $('#tool-new-line-errors').text('');
      $('#rail-line-new').before('<button id="rail-line-' + $('#new-rail-line-color').val().slice(1, 7) + '" class="rail-line btn-info" style="background-color: ' + $('#new-rail-line-color').val() + ';">' + $('#new-rail-line-name').val() + '</button>');
      saveMapAsObject();
    }

    // Re-bind events to .rail-line -- otherwise, newly created lines won't have events
    bindRailLineEvents();

  })

  $('#station-name').change(function() {
    // Get the coordinates where this station was placed
    // Use this to pre-populate which line this station services
    
    // Remove characters that are invalid for an HTML DOM ID
    // $(this).val($(this).val().replaceAll('"', '').replaceAll("'", '').replaceAll('<', '').replaceAll('>', '').replaceAll('&', '').replaceAll('/', '').replaceAll('`', ''))
    $(this).val($(this).val().replace(/[^A-Za-z0-9\- ]/g, ''));

    var x = $('#station-coordinates-x').val();
    var y = $('#station-coordinates-y').val();
    if (x >= 0 && y >= 0 ) {
      $('#coord-x-' + x + '-y-' + y + ' .station').attr('id', $('#station-name').val().replaceAll(' ', '_'));
      $('#coord-x-' + x + '-y-' + y + ' .station').attr('data-toggle', 'tooltip');
      $('#coord-x-' + x + '-y-' + y + ' .station').attr('title', $('#station-name').val()).tooltip('fixTitle').tooltip('show');

      setTimeout(function() {
        // Hide newly-created station name tooltip after 2 seconds
        // So you don't have to mouse over it to clear, but
        // it still shows for long enough to be useful
        $('#coord-x-' + x + '-y-' + y + ' .station').tooltip('hide');
      }, 2000);
    }

    saveMapAsObject();
  });

  $('#station-name-orientation').change(function() {
    var x = $('#station-coordinates-x').val();
    var y = $('#station-coordinates-y').val();

    $('#coord-x-' + x + '-y-' + y + ' .station').removeClass('rot45').removeClass('rot-45').removeClass('rot180').removeClass('rot135');

    if (x >= 0 && y >= 0) {
      if ($(this).val() == '0') {
        // Default orientation, no class needed.
      } else if ($(this).val() == '-45') {
        $('#coord-x-' + x + '-y-' + y + ' .station').addClass('rot-45');
      } else if ($(this).val() == '45') {
        $('#coord-x-' + x + '-y-' + y + ' .station').addClass('rot45');
      } else if ($(this).val() == '180') {
        $('#coord-x-' + x + '-y-' + y + ' .station').addClass('rot180');
      } else if ($(this).val() == '135') {
        $('#coord-x-' + x + '-y-' + y + ' .station').addClass('rot135');
      }
    }

    window.localStorage.setItem('metroMapStationOrientation', $(this).val());
  });

  $('#station-transfer').click(function() {
    // Get the coordinates where this station was placed
    // Use this to pre-populate which line this station services

    var x = $('#station-coordinates-x').val();
    var y = $('#station-coordinates-y').val();
    if (x >= 0 && y >= 0 ) {
      if ($(this).is(':checked')) {
         $('#coord-x-' + x + '-y-' + y + ' .station').addClass('transfer-station');
      } else {
         $('#coord-x-' + x + '-y-' + y + ' .station').removeClass('transfer-station');
      }
    }
  });

});
