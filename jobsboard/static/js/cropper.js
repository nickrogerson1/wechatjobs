const getCenterPointToIntersectionDistance = (cropCenterX, cropCenterY, cropDirectionPointX, cropDirectionPointY, linePointX1, linePointY1, linePointX2, linePointY2) => {
    const intersectionPoint = intersect(cropCenterX, cropCenterY, cropDirectionPointX, cropDirectionPointY, linePointX1, linePointY1, linePointX2, linePointY2);
    if (intersectionPoint) {
        const distance = Math.sqrt(Math.pow(intersectionPoint.x - cropCenterX, 2) + Math.pow(intersectionPoint.y - cropCenterY, 2));
        return distance;
    }
    return false;
}

/* line intercept math by Paul Bourke http://paulbourke.net/geometry/pointlineplane/
/ Determine the intersection point of two line segments
/ Return FALSE if the lines don't intersect */
const intersect = (x1, y1, x2, y2, x3, y3, x4, y4) => {
    if ((x1 === x2 && y1 === y2) || (x3 === x4 && y3 === y4)) return false ; // Zero length line
    const denominator = ((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1));
    if (denominator === 0) return false; // Lines are parallel
    let ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denominator
    let x = x1 + ua * (x2 - x1)
    let y = y1 + ua * (y2 - y1)
    return {x, y}
}

const cropperToFilePondEditorOutput = (cropper) => {
    const canvasData = cropper.getCanvasData() 
    const cropData = cropper.getData()
    const imageData = cropper.getImageData()

    /* coordinates of each corner of the original image with the origin at the center of the canvas (rotation point) */
    const offsetTopLeftX =  -imageData.naturalWidth/2;
    const offsetTopLeftY =  -imageData.naturalHeight/2;
    const offsetTopRightX =  imageData.naturalWidth/2;
    const offsetTopRightY =  -imageData.naturalHeight/2;
    const offsetBottomLeftX =  -imageData.naturalWidth/2;
    const offsetBottomLeftY =  imageData.naturalHeight/2;
    const offsetBottomRightX = imageData.naturalWidth/2;
    const offsetBottomRightY = imageData.naturalHeight/2;

    /* apply rotation to each corner */
    const rotatedTopLeftX = offsetTopLeftX * Math.cos(cropData.rotate * Math.PI / 180) - offsetTopLeftY * Math.sin(cropData.rotate * Math.PI / 180);
    const rotatedTopLeftY = offsetTopLeftX * Math.sin(cropData.rotate * Math.PI / 180) + offsetTopLeftY * Math.cos(cropData.rotate * Math.PI / 180);
    const rotatedTopRightX = offsetTopRightX * Math.cos(cropData.rotate * Math.PI / 180) - offsetTopRightY * Math.sin(cropData.rotate * Math.PI / 180);
    const rotatedTopRightY = offsetTopRightX * Math.sin(cropData.rotate * Math.PI / 180) + offsetTopRightY * Math.cos(cropData.rotate * Math.PI / 180);
    const rotatedBottomLeftX = offsetBottomLeftX * Math.cos(cropData.rotate * Math.PI / 180) - offsetBottomLeftY * Math.sin(cropData.rotate * Math.PI / 180);
    const rotatedBottomLeftY = offsetBottomLeftX * Math.sin(cropData.rotate * Math.PI / 180) + offsetBottomLeftY * Math.cos(cropData.rotate * Math.PI / 180);
    const rotatedBottomRightX = offsetBottomRightX * Math.cos(cropData.rotate * Math.PI / 180) - offsetBottomRightY * Math.sin(cropData.rotate * Math.PI / 180);
    const rotatedBottomRightY = offsetBottomRightX * Math.sin(cropData.rotate * Math.PI / 180) + offsetBottomRightY * Math.cos(cropData.rotate * Math.PI / 180);

    /* offset coordinates so origin is the top left corner of the rotated canvas (ie use canvasData width and height) */
    const translatedTopLeftX = rotatedTopLeftX + canvasData.naturalWidth/2;
    const translatedTopLeftY = rotatedTopLeftY + canvasData.naturalHeight/2;
    const translatedTopRightX = rotatedTopRightX + canvasData.naturalWidth/2;
    const translatedTopRightY = rotatedTopRightY + canvasData.naturalHeight/2;
    const translatedBottomLeftX = rotatedBottomLeftX + canvasData.naturalWidth/2;
    const translatedBottomLeftY = rotatedBottomLeftY + canvasData.naturalHeight/2;
    const translatedBottomRightX = rotatedBottomRightX + canvasData.naturalWidth/2;
    const translatedBottomRightY = rotatedBottomRightY + canvasData.naturalHeight/2;

    /* Center point of crop area in rotated coordinates */
    let centerX = cropData.x + cropData.width / 2
    let centerY = cropData.y + cropData.height / 2


    let distances = [];

    distances.push(getCenterPointToIntersectionDistance(centerX, centerY, centerX + cropData.width/2, centerY + cropData.height/2, translatedTopLeftX, translatedTopLeftY, translatedTopRightX, translatedTopRightY ));
    distances.push(getCenterPointToIntersectionDistance(centerX, centerY, centerX + cropData.width/2, centerY + cropData.height/2, translatedTopLeftX, translatedTopLeftY, translatedBottomLeftX, translatedBottomLeftY ));
    distances.push(getCenterPointToIntersectionDistance(centerX, centerY, centerX + cropData.width/2, centerY + cropData.height/2, translatedBottomLeftX, translatedBottomLeftY, translatedBottomRightX, translatedBottomRightY ));
    distances.push(getCenterPointToIntersectionDistance(centerX, centerY, centerX + cropData.width/2, centerY + cropData.height/2, translatedTopRightX, translatedTopRightY, translatedBottomRightX, translatedBottomRightY ));

    distances.push(getCenterPointToIntersectionDistance(centerX, centerY, centerX + cropData.width/2, centerY - cropData.height/2, translatedTopLeftX, translatedTopLeftY, translatedTopRightX, translatedTopRightY ));
    distances.push(getCenterPointToIntersectionDistance(centerX, centerY, centerX + cropData.width/2, centerY - cropData.height/2, translatedTopLeftX, translatedTopLeftY, translatedBottomLeftX, translatedBottomLeftY ));
    distances.push(getCenterPointToIntersectionDistance(centerX, centerY, centerX + cropData.width/2, centerY - cropData.height/2, translatedBottomLeftX, translatedBottomLeftY, translatedBottomRightX, translatedBottomRightY ));
    distances.push(getCenterPointToIntersectionDistance(centerX, centerY, centerX + cropData.width/2, centerY - cropData.height/2, translatedTopRightX, translatedTopRightY, translatedBottomRightX, translatedBottomRightY ));

    // remove false values from array
    distances = distances.filter(function (el) { return el !== false; });

    let shortestDistance = Math.min(...distances);
    // gets the zoom from shortest distance and half diagonal of crop area
    let zoom = shortestDistance / Math.sqrt(Math.pow(cropData.width/2, 2) + Math.pow(cropData.height/2, 2));

    /* Center point in the non-rotated image coordinates (for filepond) */

    /* offset coordinates so origin is the center of the canvas (rotation point) */
    const offsetX = centerX - canvasData.naturalWidth/2;
    const offsetY = centerY - canvasData.naturalHeight/2;

    /* apply reverse rotation to the point */
    const rotatedX = offsetX * Math.cos(-cropData.rotate * Math.PI / 180) - offsetY * Math.sin(-cropData.rotate * Math.PI / 180);
    const rotatedY = offsetX * Math.sin(-cropData.rotate * Math.PI / 180) + offsetY * Math.cos(-cropData.rotate * Math.PI / 180);

    /* offset coordinates so origin is the top left corner of the unrotated canvas (ie use imageData width and height) */
    const translatedX = rotatedX + imageData.naturalWidth/2;
    const translatedY = rotatedY + imageData.naturalHeight/2;

    centerX = translatedX;
    centerY = translatedY;

    /* Ratio of selected crop area. */
    const cropAreaRatio = cropData.height / cropData.width

    /* Center point mapped to a [0,1] range (that's what filepond waits for) */
    const mappedCenterX = centerX / imageData.naturalWidth;
    const mappedCenterY = centerY / imageData.naturalHeight;

    const filepondCropData = {
        data: {
            crop: {
                center: {
                    x: mappedCenterX,
                    y: mappedCenterY
                },
                flip: {
                    horizontal: cropData.scaleX < 0,
                    vertical: cropData.scaleY < 0
                },
                zoom,
                rotation: (Math.PI / 180) * cropData.rotate,
                aspectRatio: cropAreaRatio
            }
        }
    }
    console.log(filepondCropData)
    return filepondCropData;
}



const editor = {
    // Called by FilePond to edit the image
    // - should open your image editor
    // - receives file object and image edit instructions
    open: function (file, instructions) {
        
        console.log(this)
        const pond = this
        // open editor here
        const editor = document.createElement('div');
            editor.style.position = 'fixed';
            editor.style.left = 0;
            editor.style.right = 0;
            editor.style.top = 0;
            editor.style.bottom = 0;
            editor.style.zIndex = 9999;
            editor.style.backgroundColor = '#000';
        document.body.appendChild(editor);

        const confirmButton = document.createElement('button')
            confirmButton.className = 'cropper-buttons'
            confirmButton.style.top = '10px'
            confirmButton.innerHTML = '<span class="fa fa-check"></span>';
        editor.appendChild(confirmButton);

        const cancelButton = document.createElement('button')
            cancelButton.className = 'cropper-buttons'
            cancelButton.style.backgroundColor = 'red'
            cancelButton.style.top = '70px'
            cancelButton.innerHTML = '<span class="fa fa-close"></span>';
        editor.appendChild(cancelButton);

        const rotateButton = document.createElement('button')
            rotateButton.className = 'cropper-buttons'
            rotateButton.style.top = '130px'
            rotateButton.innerHTML = '<span class="fa fa-refresh"></span>';
        editor.appendChild(rotateButton);

        const zoomInButton  = document.createElement('button')
            zoomInButton.className = 'cropper-buttons'
            zoomInButton.style.top = '190px'
            zoomInButton.innerHTML = '<span class="fa fa-search-plus"></span>';
        editor.appendChild(zoomInButton );

        const zoomOutButton = document.createElement('button')
            zoomOutButton.className = 'cropper-buttons'
            zoomOutButton.style.top = '250px'
            zoomOutButton.innerHTML = '<span class="fa fa-search-minus"></span>';
        editor.appendChild(zoomOutButton);

        const image = new Image();
        // console.log(image)
        image.src = URL.createObjectURL(file)
        // console.log(image)
        
        editor.appendChild(image)
        const cropper = new Cropper(image, { aspectRatio: 1});
        // console.log(cropper)

        confirmButton.addEventListener('click', function() {
            const croppedInfo = cropperToFilePondEditorOutput(cropper)
            pond.onconfirm(croppedInfo)
        
        // Remove the editor from the view
        document.body.removeChild(editor);  
        });

        cancelButton.addEventListener('click', function() {
        // Remove the editor from the view
        document.body.removeChild(editor);  
        });

        rotateButton.addEventListener('click', function() {
            cropper.rotate(90)
        });

        zoomInButton.addEventListener('click', function() {
            cropper.zoom(0.2)
        });

        zoomOutButton.addEventListener('click', function() {
            cropper.zoom(-0.2)
        });

    },
    // Callback set by FilePond
    // - should be called by the editor when user confirms editing
    // - should receive output object, resulting edit information
    onconfirm: (output) => {
        // console.log(output)
    // Only do this if in candidate's profile
        if(location.pathname === '/edit-candidate-media/'){
        // Only one image for the profile pic
            const { id } = $('.pond').filepond('getFiles')[0][0]
            uploaded[id] = 'loading'
            }
        //Then disable the btn
        $('.upload-btn').attr('disabled','');
    },
    // Callback set by FilePond
    // - should be called by the editor when user cancels editing
    oncancel: () => {},

    // Callback set by FilePond
    // - should be called by the editor when user closes the editor
    onclose: () => {},
};




