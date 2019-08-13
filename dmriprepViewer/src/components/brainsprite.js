/* eslint-disable */
function brainsprite(params) {

  // Function to add nearest neighbour interpolation to a canvas
  function setNearestNeighbour(context,flag){
    context.imageSmoothingEnabled = flag;
    return context;
  }

  // Initialize the brain object
  var brain = {};

  // Initialize the brain object
  var defaultParams = {
     // Flag for "NaN" image values, i.e. unable to read values
    nanValue: false,

     // Smoothing of the main slices
    smooth: false,

     // Draw (or not) the current value
     flagValue: false,

     // Background color for the canvas
    colorBackground: '#000000',

    // Flag to turn on/off slice numbers
    flagCoordinates: false,

    // Origins and voxel size
    origin: { X: 0, Y: 0, Z: 0 },
    voxelSize: 1,

    // Affine transformation
    affine: false,

    // Colorbar size parameters
    heightColorBar: 0.04,

    // Font parameters
    sizeFont: 0.075,
    colorFont: '#FFFFFF',

    // Number of decimals displayed
    nbDecimals: 3,

    // Flag to turn on/off the crosshair
    crosshair: false,

    // Color of the crosshair
    colorCrosshair: "#0000FF",

    // Size crosshair - percentage of the field of view
    sizeCrosshair: 0.9,

    // Optional title for the viewer
    title: false,

    // Coordinates for the initial cut
    numSlice: false,
  }

  var brain = Object.assign({}, defaultParams, params);

  // Build affine, if not specified
  if (typeof brain.affine === 'boolean' && brain.affine === false) {
    brain.affine = [[brain.voxelSize , 0 , 0 , -brain.origin.X],
                    [0 , brain.voxelSize , 0 , -brain.origin.Y],
                    [0 , 0 , brain.voxelSize , -brain.origin.Z],
                    [0 , 0 , 0               , 1]]

  }

  // The main canvas, where the three slices are drawn
  brain.canvas = document.getElementById(params.canvas);
  brain.context = brain.canvas.getContext('2d');
  brain.context = setNearestNeighbour(brain.context,brain.smooth);

  // An in-memory canvas to draw intermediate reconstruction
  // of the coronal slice, at native resolution
  brain.canvasY = document.createElement('canvas');
  brain.contextY = brain.canvasY.getContext('2d');

  // An in-memory canvas to draw intermediate reconstruction
  // of the axial slice, at native resolution
  brain.canvasZ = document.createElement('canvas');
  brain.contextZ = brain.canvasZ.getContext('2d');

  // An in-memory canvas to read the value of pixels
  brain.canvasRead = document.createElement('canvas');
  brain.contextRead = brain.canvasRead.getContext('2d');
  brain.canvasRead.width = 1;
  brain.canvasRead.height = 1;

  // Onclick events
  brain.onclick = typeof params.onclick !== 'undefined' ? params.onclick : "";

  // Font parameters
  if (brain.flagCoordinates) {
    brain.spaceFont = 0.1;
  } else {
    brain.spaceFont = 0;
  };

  //******************//
  // The sprite image //
  //******************//
  brain.sprite = document.getElementById(params.sprite);

  // Number of columns and rows in the sprite
  brain.nbCol = brain.sprite.width/params.nbSlice.Y;
  brain.nbRow = brain.sprite.height/params.nbSlice.Z;
  // Number of slices

  brain.nbSlice = {
    X: typeof params.nbSlice.X !== 'undefined' ? params.nbSlice.X : brain.nbCol*brain.nbRow,
    Y: params.nbSlice.Y,
    Z: params.nbSlice.Z
  };

  // width and height for the canvas
  brain.widthCanvas  = {'X':0 , 'Y':0 , 'Z':0 };
  brain.heightCanvas = {'X':0 , 'Y':0 , 'Z':0 , 'max':0};

  // the slice numbers
  if (brain.numSlice == false) {
    brain.numSlice = { X: Math.floor(brain.nbSlice.X/2),
                       Y: Math.floor(brain.nbSlice.Y/2),
                       Z: Math.floor(brain.nbSlice.Z/2)}
  };

  // Coordinates for current slices - these will get updated when drawing the slices
  brain.coordinatesSlice = {'X': 0, 'Y': 0, 'Z': 0 };

  //*************//
  // The planes  //
  //*************//
  brain.planes = {};
  // A master sagital canvas for the merge of background and overlay
  brain.planes.canvasMaster = document.createElement('canvas');
  brain.planes.contextMaster = brain.planes.canvasMaster.getContext('2d');

  //*************//
  // The overlay //
  //*************//
  params.overlay = typeof params.overlay !== 'undefined' ? params.overlay : false;
  if (params.overlay) {
      // Initialize the overlay
      brain.overlay = {};
      // Get the sprite
      brain.overlay.sprite = document.getElementById(params.overlay.sprite);
      // Ratio between the resolution of the foreground and background
      // Number of columns and rows in the overlay
      brain.overlay.nbCol = brain.overlay.sprite.width/params.overlay.nbSlice.Y;
      brain.overlay.nbRow = brain.overlay.sprite.height/params.overlay.nbSlice.Z;
      // Number of slices in the overlay
      brain.overlay.nbSlice = {
        X: typeof params.overlay.nbSlice.X !== 'undefined' ? params.overlay.nbSlice.X : brain.overlay.nbCol*brain.overlay.nbRow,
        Y: params.overlay.nbSlice.Y,
        Z: params.overlay.nbSlice.Z
      };
      // opacity
      brain.overlay.opacity = typeof params.overlay.opacity !== 'undefined' ? params.overlay.opacity : 1;
  };

  //**************//
  // The colormap //
  //**************//
  params.colorMap = typeof params.colorMap !== 'undefined' ? params.colorMap: false;
  if (params.colorMap) {
      // Initialize the color map
      brain.colorMap = {};
      // Get the sprite
      brain.colorMap.img = document.getElementById(params.colorMap.img);
      // Set min / max
      brain.colorMap.min = params.colorMap.min;
      brain.colorMap.max = params.colorMap.max;
      // Set visibility
      params.colorMap.hide = typeof params.colorMap.hide !== 'undefined' ? params.colorMap.hide: false;
      // An in-memory canvas to store the colormap
      brain.colorMap.canvas = document.createElement('canvas');
      brain.colorMap.context = brain.colorMap.canvas.getContext('2d');
      brain.colorMap.canvas.width  = brain.colorMap.img.width;
      brain.colorMap.canvas.height = brain.colorMap.img.height;

      // Copy the color map in an in-memory canvas
      brain.colorMap.context.drawImage(brain.colorMap.img,
                0,0,brain.colorMap.img.width, brain.colorMap.img.height,
                0,0,brain.colorMap.img.width, brain.colorMap.img.height);
  };

  //*******************************************//
  // Extract the value associated with a voxel //
  //*******************************************//
  brain.getValue = function(rgb,colorMap) {
    if (!colorMap) {
      return NaN;
    }
    var cv, dist, nbColor, ind, val, voxelValue;
    nbColor = colorMap.canvas.width;
    ind = NaN;
    val = Infinity;
    for (let xx=0; xx<nbColor; xx++) {
      cv = colorMap.context.getImageData(xx,0,1,1).data;
      dist = Math.pow(cv[0]-rgb[0],2)+Math.pow(cv[1]-rgb[1],2)+Math.pow(cv[2]-rgb[2],2);
      if (dist<val) {
        ind = xx;
        val = dist;
      }
    }
    voxelValue = (ind*(colorMap.max - colorMap.min)/(nbColor-1)) + colorMap.min;
    return voxelValue;
  };


  //***************************************//
  // Update voxel value                    //
  //***************************************//
  brain.updateValue = function() {
    var pos={};
    var test1=[];
    var test2=[];
    if (brain.overlay && !brain.nanValue) {
      try {
        pos.XW = Math.round((brain.numSlice.X) % brain.nbCol);
        pos.XH = Math.round((brain.numSlice.X - pos.XW) / brain.nbCol);
        brain.contextRead.fillStyle='#FFFFFF';
        brain.contextRead.fillRect(0, 0, 1, 1);
        brain.contextRead.drawImage(brain.overlay.sprite,
                                    pos.XW*brain.nbSlice.Y+brain.numSlice.Y,
                                    pos.XH*brain.nbSlice.Z+brain.nbSlice.Z-brain.numSlice.Z-1,
                                    1, 1, 0, 0, 1, 1);
        let rgb = brain.contextRead.getImageData(0,0,1,1).data;
        test1 = ( (rgb[0] == 255) && (rgb[1]==255) && (rgb[2]==255));
        brain.contextRead.fillStyle='#000000';
        brain.contextRead.fillRect(0, 0, 1, 1);
        brain.contextRead.drawImage(brain.overlay.sprite,
                                    pos.XW*brain.nbSlice.Y+brain.numSlice.Y,
                                    pos.XH*brain.nbSlice.Z+brain.nbSlice.Z-brain.numSlice.Z-1,
                                    1, 1, 0, 0, 1, 1 );
        rgb = brain.contextRead.getImageData(0,0,1,1).data;
        test2 = ( (rgb[0] == 0) && (rgb[1]==0) && (rgb[2]==0));
        if (test1&&test2){
          brain.voxelValue = NaN
        }
        else {
          brain.voxelValue = brain.getValue(rgb,brain.colorMap);
        }
      }
      catch(err) {
        console.warn(err.message);
        rgb = 0;
        brain.nanValue = true;
        brain.voxelValue = NaN;
      }
    } else {
      brain.voxelValue = NaN;
    };
  };


  //***************************************//
  // Multiply two matrices                 //
  //***************************************//
  // Snippet copied from https://stackoverflow.com/questions/27205018/multiply-2-matrices-in-javascript
  brain.multiply = function (a, b) {
    var aNumRows = a.length, aNumCols = a[0].length,
        bNumRows = b.length, bNumCols = b[0].length,
        m = new Array(aNumRows);  // initialize array of rows
    for (var r = 0; r < aNumRows; ++r) {
      m[r] = new Array(bNumCols); // initialize the current row
      for (var c = 0; c < bNumCols; ++c) {
        m[r][c] = 0;             // initialize the current cell
        for (var i = 0; i < aNumCols; ++i) {
          m[r][c] += a[r][i] * b[i][c];
        }
      }
    }
    return m;
  }


  //***************************************//
  // Update slice coordinates              //
  //***************************************//
  brain.updateCoordinates = function() {
    const coordVoxel = brain.multiply(brain.affine,
                  [ [brain.numSlice.X+1] ,
                    [brain.numSlice.Y+1] ,
                    [brain.numSlice.Z+1] ,
                    [1] ]);
    brain.coordinatesSlice.X = coordVoxel[0];
    brain.coordinatesSlice.Y = coordVoxel[1];
    brain.coordinatesSlice.Z = coordVoxel[2];
  };


  //***********************//
  // Initialize the viewer //
  //***********************//
  brain.init = function() {

    // Update the width of the X, Y and Z slices in the canvas, based on the width of its parent
    brain.widthCanvas.X = Math.floor(brain.canvas.parentElement.clientWidth*(brain.nbSlice.Y/(2*brain.nbSlice.X+brain.nbSlice.Y)));
    brain.widthCanvas.Y = Math.floor(brain.canvas.parentElement.clientWidth*(brain.nbSlice.X/(2*brain.nbSlice.X+brain.nbSlice.Y)));
    brain.widthCanvas.Z = Math.floor(brain.canvas.parentElement.clientWidth*(brain.nbSlice.X/(2*brain.nbSlice.X+brain.nbSlice.Y)));
    brain.widthCanvas.max = Math.max(brain.widthCanvas.X,brain.widthCanvas.Y,brain.widthCanvas.Z);

    // Update the height of the slices in the canvas, based on width and image ratio
    brain.heightCanvas.X = Math.floor(brain.widthCanvas.X * brain.nbSlice.Z / brain.nbSlice.Y );
    brain.heightCanvas.Y = Math.floor(brain.widthCanvas.Y * brain.nbSlice.Z / brain.nbSlice.X );
    brain.heightCanvas.Z = Math.floor(brain.widthCanvas.Z * brain.nbSlice.Y / brain.nbSlice.X );
    brain.heightCanvas.max = Math.max(brain.heightCanvas.X,brain.heightCanvas.Y,brain.heightCanvas.Z);

    // Apply the width/height to the canvas, if necessary
    if (brain.canvas.width!=(brain.widthCanvas.X+brain.widthCanvas.Y+brain.widthCanvas.Z)) {
      brain.canvas.width = brain.widthCanvas.X+brain.widthCanvas.Y+brain.widthCanvas.Z;
      brain.canvas.height = Math.round((1+brain.spaceFont)*(brain.heightCanvas.max));
      brain.context = setNearestNeighbour(brain.context,brain.smooth);
    };

    // Size for fonts
    brain.sizeFontPixels = Math.round(brain.sizeFont*(brain.heightCanvas.max));

    // fonts
    brain.context.font = brain.sizeFontPixels + "px Arial";

    // Draw the Master canvas
    brain.planes.canvasMaster.width = brain.sprite.width;
    brain.planes.canvasMaster.height = brain.sprite.height;
    brain.planes.contextMaster.globalAlpha = 1;
    brain.planes.contextMaster.drawImage(brain.sprite,
            0, 0, brain.sprite.width, brain.sprite.height,0, 0, brain.sprite.width, brain.sprite.height );
    if (brain.overlay) {
        // Draw the overlay on a canvas
        brain.planes.contextMaster.globalAlpha = brain.overlay.opacity;
        brain.planes.contextMaster.drawImage(brain.overlay.sprite,
            0, 0, brain.overlay.sprite.width, brain.overlay.sprite.height,0,0,brain.sprite.width,brain.sprite.height);
    };

    // Draw the X canvas (sagital)
    brain.planes.canvasX = document.createElement('canvas');
    brain.planes.contextX = brain.planes.canvasX.getContext('2d');
    brain.planes.canvasX.width  = brain.nbSlice.Y;
    brain.planes.canvasX.height = brain.nbSlice.Z;

    // Draw the Y canvas (coronal)
    brain.planes.canvasY = document.createElement('canvas');
    brain.planes.contextY = brain.planes.canvasY.getContext('2d');
    brain.planes.canvasY.width  = brain.nbSlice.X;
    brain.planes.canvasY.height = brain.nbSlice.Z;

    // Draw the Z canvas (axial)
    brain.planes.canvasZ = document.createElement('canvas');
    brain.planes.contextZ = brain.planes.canvasZ.getContext('2d');
    brain.planes.canvasZ.width = brain.nbSlice.X;
    brain.planes.canvasZ.height = brain.nbSlice.Y;
    brain.planes.contextZ.rotate(-Math.PI/2);
    brain.planes.contextZ.translate(-brain.nbSlice.Y,0);

    // Update value
    brain.updateValue()

    // Update coordinates
    brain.updateCoordinates()

    // Round up slice coordinates
    brain.numSlice.X = Math.round(brain.numSlice.X)
    brain.numSlice.Y = Math.round(brain.numSlice.Y)
    brain.numSlice.Z = Math.round(brain.numSlice.Z)

  }


  //***************************************//
  // Draw a particular slice in the canvas //
  //***************************************//
  brain.draw = function(slice,type) {

    // Init variables
    var pos={}, coord, coordWidth, offset={X:'',Y:'',Z:''};
    offset.X = Math.ceil((1-brain.sizeCrosshair)*brain.nbSlice.X/2)
    offset.Y = Math.ceil((1-brain.sizeCrosshair)*brain.nbSlice.Y/2)
    offset.Z = Math.ceil((1-brain.sizeCrosshair)*brain.nbSlice.Z/2)

    // Now draw the slice
    switch(type) {
      case 'X':
        // Draw a sagital slice in memory
        pos.XW = ((brain.numSlice.X)%brain.nbCol);
        pos.XH = (brain.numSlice.X-pos.XW)/brain.nbCol;
        brain.planes.contextX.drawImage(brain.planes.canvasMaster,
                pos.XW*brain.nbSlice.Y, pos.XH*brain.nbSlice.Z, brain.nbSlice.Y, brain.nbSlice.Z,0, 0, brain.nbSlice.Y, brain.nbSlice.Z );

        // Add a crosshair
        if (brain.crosshair) {
          brain.planes.contextX.fillStyle = brain.colorCrosshair;
          brain.planes.contextX.fillRect( brain.numSlice.Y, offset.Z , 1 , brain.nbSlice.Z-2*offset.Z );
          brain.planes.contextX.fillRect( offset.Y, brain.nbSlice.Z-brain.numSlice.Z-1, brain.nbSlice.Y-2*offset.Y , 1 );
        }

        // fill the slice with background color
        brain.context.fillStyle=brain.colorBackground;
        brain.context.fillRect(0, 0, brain.widthCanvas.X , brain.canvas.height);

        // Draw on the main canvas
        brain.context.drawImage(brain.planes.canvasX,
                0, 0, brain.nbSlice.Y, brain.nbSlice.Z,0, (brain.heightCanvas.max-brain.heightCanvas.X)/2, brain.widthCanvas.X, brain.heightCanvas.X );

        // Draw the title
        if (brain.title) {
          brain.context.fillStyle = brain.colorFont;
          brain.context.fillText(brain.title,Math.round(brain.widthCanvas.X/10),Math.round( (brain.heightCanvas.max*brain.heightColorBar) + (1/4)*(brain.sizeFontPixels)));
        }

        // Draw the value at current voxel
        if (brain.flagValue) {
          value = "value = "+Number.parseFloat(brain.voxelValue).toPrecision(brain.nbDecimals).replace(/0+$/,"")
          valueWidth = brain.context.measureText(value).width;
          brain.context.fillStyle = brain.colorFont;
          brain.context.fillText(value,Math.round(brain.widthCanvas.X/10),Math.round( (brain.heightCanvas.max*brain.heightColorBar*2) + (3/4)*(brain.sizeFontPixels)));
        }

        // Add X coordinates on the slice
        if (brain.flagCoordinates) {
          coord = "x = "+Math.round(brain.coordinatesSlice.X);
          coordWidth = brain.context.measureText(coord).width;
          brain.context.fillStyle = brain.colorFont;
          brain.context.fillText(coord,brain.widthCanvas.X/2-coordWidth/2,Math.round(brain.canvas.height-(brain.sizeFontPixels/2)));
        }
      break;

      case 'Y':
        // Draw a single coronal slice at native resolution
        brain.context.fillStyle=brain.colorBackground;
        brain.context.fillRect(brain.widthCanvas.X, 0, brain.widthCanvas.Y, brain.canvas.height);
        for (let xx=0; xx<brain.nbSlice.X; xx++) {
          const posW = (xx%brain.nbCol);
          const posH = (xx-posW)/brain.nbCol;
          brain.planes.contextY.drawImage(brain.planes.canvasMaster,
              posW*brain.nbSlice.Y + brain.numSlice.Y, posH*brain.nbSlice.Z, 1, brain.nbSlice.Z, xx, 0, 1, brain.nbSlice.Z );
        }

        // Add a crosshair
        if (brain.crosshair) {
          brain.planes.contextY.fillStyle = brain.colorCrosshair;
          brain.planes.contextY.fillRect( brain.numSlice.X, offset.Z , 1 , brain.nbSlice.Z-2*offset.Z );
          brain.planes.contextY.fillRect( offset.X, brain.nbSlice.Z-brain.numSlice.Z-1 , brain.nbSlice.X-2*offset.X , 1 );
        }

        // Redraw the coronal slice in the canvas at screen resolution
        brain.context.drawImage(brain.planes.canvasY,
          0, 0, brain.nbSlice.X, brain.nbSlice.Z, brain.widthCanvas.X, (brain.heightCanvas.max-brain.heightCanvas.Y)/2, brain.widthCanvas.Y, brain.heightCanvas.Y );

        // Add colorbar
        if ((brain.colorMap)&&(!brain.colorMap.hide)) {
          // draw the colorMap on the coronal slice at screen resolution
          brain.context.drawImage(brain.colorMap.img,
                0, 0, brain.colorMap.img.width, 1, Math.round(brain.widthCanvas.X + brain.widthCanvas.Y*0.2) , Math.round(brain.heightCanvas.max * brain.heightColorBar / 2), Math.round(brain.widthCanvas.Y*0.6) , Math.round(brain.heightCanvas.max * brain.heightColorBar));
          brain.context.fillStyle = brain.colorFont;
          label_min = Number.parseFloat(brain.colorMap.min).toPrecision(brain.nbDecimals).replace(/0+$/,"")
          label_max = Number.parseFloat(brain.colorMap.max).toPrecision(brain.nbDecimals).replace(/0+$/,"")
          brain.context.fillText(label_min,brain.widthCanvas.X+(brain.widthCanvas.Y*0.2)-brain.context.measureText(label_min).width/2,Math.round( (brain.heightCanvas.max*brain.heightColorBar*2) + (3/4)*(brain.sizeFontPixels) ));
          brain.context.fillText(label_max,brain.widthCanvas.X+(brain.widthCanvas.Y*0.8)-brain.context.measureText(label_max).width/2,Math.round( (brain.heightCanvas.max*brain.heightColorBar*2) + (3/4)*(brain.sizeFontPixels) ));
        }

        // Add Y coordinates on the slice
        if (brain.flagCoordinates) {
          brain.context.font = brain.sizeFontPixels + "px Arial";
          brain.context.fillStyle = brain.colorFont;
          coord = "y = "+Math.round(brain.coordinatesSlice.Y);
          coordWidth = brain.context.measureText(coord).width;
          brain.context.fillText(coord,brain.widthCanvas.X+(brain.widthCanvas.Y/2)-coordWidth/2,Math.round(brain.canvas.height-(brain.sizeFontPixels/2)));
        }

      case 'Z':
        // Draw a single axial slice at native resolution
        brain.context.fillStyle=brain.colorBackground;
        brain.context.fillRect(brain.widthCanvas.X+brain.widthCanvas.Y, 0, brain.widthCanvas.Z, brain.canvas.height);

        for (let xx=0; xx<brain.nbSlice.X; xx++) {
          const posW = (xx%brain.nbCol);
          const posH = (xx-posW)/brain.nbCol;
          brain.planes.contextZ.drawImage(brain.planes.canvasMaster,
              posW*brain.nbSlice.Y , posH*brain.nbSlice.Z + brain.nbSlice.Z-brain.numSlice.Z-1, brain.nbSlice.Y, 1, 0, xx, brain.nbSlice.Y, 1 );
        }

        // Add a crosshair
        if (brain.crosshair) {
          brain.planes.contextZ.fillStyle = brain.colorCrosshair;
          brain.planes.contextZ.fillRect( offset.Y,  brain.numSlice.X , brain.nbSlice.Y-2*offset.Y , 1 );
          brain.planes.contextZ.fillRect( brain.numSlice.Y , offset.X , 1, brain.nbSlice.X-2*offset.X );
        }

        // Redraw the axial slice in the canvas at screen resolution
        brain.context.drawImage(brain.planes.canvasZ,
          0, 0, brain.nbSlice.X, brain.nbSlice.Y, brain.widthCanvas.X+brain.widthCanvas.Y, (brain.heightCanvas.max-brain.heightCanvas.Z)/2, brain.widthCanvas.Z, brain.heightCanvas.Z );

        // Add Z coordinates on the slice
        if (brain.flagCoordinates) {
          coord = "z = "+Math.round(brain.coordinatesSlice.Z);
          coordWidth = brain.context.measureText(coord).width;
          brain.context.fillStyle = brain.colorFont;
          brain.context.fillText(coord,brain.widthCanvas.X+brain.widthCanvas.Y+(brain.widthCanvas.Z/2)-coordWidth/2,Math.round(brain.canvas.height-(brain.sizeFontPixels/2)));
        }
    }
  };

  // In case of click, update brain slices
  brain.clickBrain = function(e){
    var rect = brain.canvas.getBoundingClientRect();
    var xx = e.clientX - rect.left;
    var yy = e.clientY - rect.top;
    var sx, sy, sz;

    if (xx<brain.widthCanvas.X){
      sy = Math.round((brain.nbSlice.Y-1)*(xx/brain.widthCanvas.X));
      sz = Math.round((brain.nbSlice.Z-1)*(((brain.heightCanvas.max+brain.heightCanvas.X)/2)-yy)/brain.heightCanvas.X);
      brain.numSlice.Y = Math.max(Math.min(sy,brain.nbSlice.Y-1),0);
      brain.numSlice.Z = Math.max(Math.min(sz,brain.nbSlice.Z-1),0);
    } else if (xx<(brain.widthCanvas.X+brain.widthCanvas.Y)) {
      xx = xx-brain.widthCanvas.X;
      sx = Math.round((brain.nbSlice.X-1)*(xx/brain.widthCanvas.Y));
      sz = Math.round((brain.nbSlice.Z-1)*(((brain.heightCanvas.max+brain.heightCanvas.X)/2)-yy)/brain.heightCanvas.X);
      brain.numSlice.X = Math.max(Math.min(sx,brain.nbSlice.X-1),0);
      brain.numSlice.Z = Math.max(Math.min(sz,brain.nbSlice.Z-1),0);
    } else {
      xx = xx-brain.widthCanvas.X-brain.widthCanvas.Y;
      sx = Math.round((brain.nbSlice.X-1)*(xx/brain.widthCanvas.Z));
      sy = Math.round((brain.nbSlice.Y-1)*(((brain.heightCanvas.max+brain.heightCanvas.Z)/2)-yy)/brain.heightCanvas.Z);
      brain.numSlice.X = Math.max(Math.min(sx,brain.nbSlice.X-1),0);
      brain.numSlice.Y = Math.max(Math.min(sy,brain.nbSlice.Y-1),0);
    };
    // Update value
    brain.updateValue()

    // Update coordinates
    brain.updateCoordinates()

    // Redraw slices
    brain.drawAll()
    if (brain.onclick) {
      brain.onclick(e);
    };
  };

  brain.drawAll = function(){
    brain.draw(brain.numSlice.X,'X');
    brain.draw(brain.numSlice.Y,'Y');
    brain.draw(brain.numSlice.Z,'Z');
  };

  // Attach a listener for clicks
  brain.canvas.addEventListener('click', brain.clickBrain, false);

  // Attach a listener on mouse down
  brain.canvas.addEventListener('mousedown', function(e) {
    brain.canvas.addEventListener('mousemove', brain.clickBrain, false);
  }, false);

  // Detach the listener on mouse up
  brain.canvas.addEventListener('mouseup', function(e) {
      brain.canvas.removeEventListener('mousemove', brain.clickBrain, false);
    }, false);

  // Draw all slices when background/overlay are loaded
  brain.sprite.addEventListener('load', function(){
    brain.init();
    brain.drawAll();
  });
  if (brain.overlay) {
    brain.overlay.sprite.addEventListener('load', function(){
      brain.init();
      brain.drawAll();
    });
  }

  // Init the viewer
  brain.init();

  // Draw all slices
  brain.drawAll();

  return brain;
};

export default brainsprite
