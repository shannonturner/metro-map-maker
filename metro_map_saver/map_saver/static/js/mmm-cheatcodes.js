// mmm-cheatcodes.js
// Functions that may not be generally useful enough to warrant inclusion
//  in metromapmaker.js, but might be interesting all the same

function combineMap(urlhash) {
  // Add the map at the urlhash to the existing map.
  // Existing map must not be overwritten by the new map.
  // I expect this will mostly be used to bring terrain into an existing map
  // but this will only work for maps that are exactly aligned, or they will look a bit silly
  $.get('/load/' + urlhash).done(function (savedMapData) {
    savedMapData = savedMapData.replaceAll(" u&#39;", "'").replaceAll("{u&#39;", '{"').replaceAll("\\[u&#39;", '["').replaceAll('&#39;', '"').replaceAll("'", '"').replaceAll('\\\\x', '&#x');
    if (savedMapData.replace(/\s/g,'').slice(0,7) == '[ERROR]') {
      console.log("[WARN] Can't combine that map!");
    } else {
      savedMapData = JSON.parse(savedMapData)

      for (var x in savedMapData) {
        for (var y in savedMapData[x]) {
          if (!activeMap[x]) {
            activeMap[x] = {y: savedMapData[x][y]}
          } else if (activeMap[x] && !activeMap[x][y]) {
            activeMap[x][y] = savedMapData[x][y]
          }
        } // for y
      } // for x

      // Must also add the globals, otherwise the map probably won't be saveable
      for (var line in savedMapData["global"]["lines"]) {
        if (!activeMap["global"]["lines"][line]) {
          activeMap["global"]["lines"][line] = savedMapData["global"]["lines"][line]
        }
      }

      getMapSize(activeMap);
      loadMapFromObject(activeMap); // Must load not with update in order to update the map lines
      drawCanvas(activeMap);
    }
  });
} // combineMap(urlhash)