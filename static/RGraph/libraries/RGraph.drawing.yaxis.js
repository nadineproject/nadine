    /**
    * o------------------------------------------------------------------------------o
    * | This file is part of the RGraph package - you can learn more at:             |
    * |                                                                              |
    * |                          http://www.rgraph.net                               |
    * |                                                                              |
    * | This package is licensed under the RGraph license. For all kinds of business |
    * | purposes there is a small one-time licensing fee to pay and for non          |
    * | commercial  purposes it is free to use. You can read the full license here:  |
    * |                                                                              |
    * |                      http://www.rgraph.net/license                           |
    * o------------------------------------------------------------------------------o
    */



    /**
    * Having this here means that the RGraph libraries can be included in any order, instead of you having
    * to include the common core library first.
    */
    if (typeof(RGraph) == 'undefined') RGraph = {};
    if (typeof(RGraph.Drawing) == 'undefined') RGraph.Drawing = {};




    /**
    * The constructor. This function sets up the object. It takes the ID (the HTML attribute) of the canvas as the
    * first argument and the X coordinate of the axis as the second
    * 
    * @param string id The canvas tag ID
    * @param number x  The X coordinate of the Y axis
    */
    RGraph.Drawing.YAxis = function (id, x)
    {
        this.id         = id;
        this.canvas     = document.getElementById(id);
        this.context    = this.canvas.getContext('2d');
        this.canvas.__object__ = this;
        this.x          = x;
        this.coords     = [];
        this.coordsText = [];


        /**
        * This defines the type of this shape
        */
        this.type = 'drawing.yaxis';


        /**
        * This facilitates easy object identification, and should always be true
        */
        this.isRGraph = true;


        /**
        * This adds a uid to the object that you can use for identification purposes
        */
        this.uid = RGraph.CreateUID();


        /**
        * This adds a UID to the canvas for identification purposes
        */
        this.canvas.uid = this.canvas.uid ? this.canvas.uid : RGraph.CreateUID();


        /**
        * This does a few things, for example adding the .fillText() method to the canvas 2D context when
        * it doesn't exist. This facilitates the graphs to be still shown in older browser (though without
        * text obviously). You'll find the function in RGraph.common.core.js
        */
        RGraph.OldBrowserCompat(this.context);


        /**
        * Some example background properties
        */
        this.properties =
        {
            'chart.gutter.top':       25,
            'chart.gutter.bottom':    25,
            'chart.min':              0,
            'chart.max':              null,
            'chart.colors':           ['black'],
            'chart.title':            '',
            'chart.title.color':      null,
            'chart.text.color':       null,
            'chart.numticks':         5,
            'chart.numlabels':        5,
            'chart.text.font':        'Arial',
            'chart.text.size':        10,
            'chart.align':            'left',
            'hart.scale.formatter':   null,
            'chart.scale.decimals':   0,
            'chart.scale.invert':     false,
            'chart.scale.zerostart':  true,
            'chart.scale.visible':    true,
            'chart.units.pre':        '',
            'chart.units.post':       '',
            'chart.linewidth':        1,
            'chart.noendtick.top':    false,
            'chart.noendtick.bottom': false,
            'chart.noyaxis':          false,
            'chart.tooltips':         null,
            'chart.tooltips.effect':   'fade',
            'chart.tooltips.css.class':'RGraph_tooltip',
            'chart.tooltips.event':    'onclick',
            'chart.xaxispos':         'bottom',
            'chart.events.click':     null,
            'chart.events.mousemove': null
        }


        /**
        * A simple check that the browser has canvas support
        */
        if (!this.canvas) {
            alert('[DRAWING.YAXIS] No canvas support');
            return;
        }
        
        /**
        * Create the dollar object so that functions can be added to them
        */
        this.$0 = {};


        /**
        * Translate half a pixel for antialiasing purposes - but only if it hasn't beeen
        * done already
        * 
        * ** Could use setTransform() here instead ?
        */
        if (!this.canvas.__rgraph_aa_translated__) {
            this.context.translate(0.5,0.5);
            
            this.canvas.__rgraph_aa_translated__ = true;
        }



        /**
        * Objects are now always registered so that the chart is redrawn if need be.
        */
        RGraph.Register(this);
    }




    /**
    * A setter method for setting graph properties. It can be used like this: obj.Set('chart.strokestyle', '#666');
    * 
    * @param name  string The name of the property to set
    * @param value mixed  The value of the property
    */
    RGraph.Drawing.YAxis.prototype.Set = function (name, value)
    {
        name = name.toLowerCase();

        /**
        * This should be done first - prepend the property name with "chart." if necessary
        */
        if (name.substr(0,6) != 'chart.') {
            name = 'chart.' + name;
        }

        this.properties[name] = value;

        return this;
    }




    /**
    * A getter method for retrieving graph properties. It can be used like this: obj.Get('chart.strokestyle');
    * 
    * @param name  string The name of the property to get
    */
    RGraph.Drawing.YAxis.prototype.Get = function (name)
    {
        /**
        * This should be done first - prepend the property name with "chart." if necessary
        */
        if (name.substr(0,6) != 'chart.') {
            name = 'chart.' + name;
        }

        return this.properties[name.toLowerCase()];
    }




    /**
    * Draws the axes
    */
    RGraph.Drawing.YAxis.prototype.Draw = function ()
    {
        /**
        * Fire the onbeforedraw event
        */
        RGraph.FireCustomEvent(this, 'onbeforedraw');

        /**
        * Some defaults
        */
        this.gutterTop    = this.properties['chart.gutter.top'];
        this.gutterBottom = this.properties['chart.gutter.bottom'];

        if (!this.properties['chart.text.color'])  this.properties['chart.text.color']  = this.properties['chart.colors'][0];
        if (!this.properties['chart.title.color']) this.properties['chart.title.color'] = this.properties['chart.colors'][0];

        /**
        * Parse the colors. This allows for simple gradient syntax
        */
        if (!this.colorsParsed) {

            this.parseColors();

            // Don't want to do this again
            this.colorsParsed = true;
        }



        // DRAW Y AXIS HERE
        this.DrawYAxis();


        /**
        * This installs the event listeners
        */
        RGraph.InstallEventListeners(this);



        /**
        * Fire the ondraw event
        */
        RGraph.FireCustomEvent(this, 'ondraw');
        
        return this;
    }



    /**
    * The getObjectByXY() worker method
    */
    RGraph.Drawing.YAxis.prototype.getObjectByXY = function (e)
    {
        if (this.getShape(e)) {
            return this;
        }
    }



    /**
    * Not used by the class during creating the axis, but is used by event handlers
    * to get the coordinates (if any) of the selected shape
    * 
    * @param object e The event object
    */
    RGraph.Drawing.YAxis.prototype.getShape = function (e)
    {
        var mouseXY = RGraph.getMouseXY(e);
        var mouseX  = mouseXY[0];
        var mouseY  = mouseXY[1];

        if (   mouseX >= this.x - (this.properties['chart.align'] ==  'left' ? this.getWidth() : 0)
            && mouseX <= this.x + (this.properties['chart.align'] ==  'left' ? 0 : this.getWidth())
            && mouseY >= this.gutterTop
            && mouseY <= (this.canvas.height - this.gutterBottom)
           ) {
            
            var x = this.x;
            var y = this.gutterTop;
            var w = 15;;
            var h = this.canvas.height - this.gutterTop - this.gutterBottom;

            return {
                    0: this, 1: x, 2: y, 3: w, 4: h, 5: 0,
                    'object': this, 'x': x, 'y': y, 'width': w, 'height': h, 'index': 0, 'tooltip': this.properties['chart.tooltips'] ? this.properties['chart.tooltips'][0] : null
                   };
        }

        return null;
    }



    /**
    * This function positions a tooltip when it is displayed
    * 
    * @param obj object    The chart object
    * @param int x         The X coordinate specified for the tooltip
    * @param int y         The Y coordinate specified for the tooltip
    * @param objec tooltip The tooltips DIV element
    */
    RGraph.Drawing.YAxis.prototype.positionTooltip = function (obj, x, y, tooltip, idx)
    {
        var coordW     = obj.properties['chart.text.size'] * 1.5;
        var coordX     = obj.x - coordW;
        var coordY     = obj.gutterTop;
        var coordH     = obj.canvas.height - obj.gutterTop - obj.gutterBottom;
        var canvasXY   = RGraph.getCanvasXY(obj.canvas);
        
        var width      = tooltip.offsetWidth;
        var height     = tooltip.offsetHeight;

        // Set the top position
        tooltip.style.left = 0;
        tooltip.style.top  = canvasXY[1] + ((this.canvas.height - this.gutterTop - this.gutterBottom) / 2) + 'px';

        // By default any overflow is hidden
        tooltip.style.overflow = '';

        // The arrow
        var img = new Image();
            img.src = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABEAAAAFCAYAAACjKgd3AAAARUlEQVQYV2NkQAN79+797+RkhC4M5+/bd47B2dmZEVkBCgcmgcsgbAaA9GA1BCSBbhAuA/AagmwQPgMIGgIzCD0M0AMMAEFVIAa6UQgcAAAAAElFTkSuQmCC';
            img.style.position = 'absolute';
            img.id = '__rgraph_tooltip_pointer__';
            img.style.top = (tooltip.offsetHeight - 2) + 'px';
        tooltip.appendChild(img);
        
        // Reposition the tooltip if at the edges:
        
        // LEFT edge
        if ((canvasXY[0] + coordX + (coordW / 2) - (width / 2)) < 10) {
            tooltip.style.left = (canvasXY[0] + coordX - (width * 0.1)) + (coordW / 2) + 'px';
            img.style.left = ((width * 0.1) - 8.5) + 'px';

        // RIGHT edge
        } else if ((canvasXY[0] + coordX + (width / 2)) > document.body.offsetWidth) {
            tooltip.style.left = canvasXY[0] + coordX - (width * 0.9) + (coordW / 2) + 'px';
            img.style.left = ((width * 0.9) - 8.5) + 'px';

        // Default positioning - CENTERED
        } else {
            tooltip.style.left = (canvasXY[0] + coordX + (coordW / 2) - (width * 0.5)) + 'px';
            img.style.left = ((width * 0.5) - 8.5) + 'px';
        }
    }



    /**
    * Each object type has its own Highlight() function which highlights the appropriate shape
    * 
    * @param object shape The shape to highlight
    */
    RGraph.Drawing.YAxis.prototype.Highlight = function (shape)
    {
        // When showing tooltips, this method can be used to highlight the X axis
    }



    /**
    * This allows for easy specification of gradients
    */
    RGraph.Drawing.YAxis.prototype.parseColors = function ()
    {
        /**
        * Parse various properties for colors
        */
        //this.properties['chart.title.color'] = this.parseSingleColorForGradient(this.properties['chart.title.color']);
        //this.properties['chart.text.color']  = this.parseSingleColorForGradient(this.properties['chart.text.color']);
        this.properties['chart.colors'][0]   = this.parseSingleColorForGradient(this.properties['chart.colors'][0]);
    }



    /**
    * This parses a single color value
    */
    RGraph.Drawing.YAxis.prototype.parseSingleColorForGradient = function (color)
    {
        var canvas  = this.canvas;
        var context = this.context;
        
        if (!color) {
            return color;
        }

        if (color.match(/^gradient\((.*)\)$/i)) {

            var parts = RegExp.$1.split(':');

            // Create the gradient
            var grad = context.createLinearGradient(0,this.properties['chart.gutter.top'],0,this.canvas.height - this.gutterBottom);

            var diff = 1 / (parts.length - 1);

            grad.addColorStop(0, RGraph.trim(parts[0]));

            for (var j=1; j<parts.length; ++j) {
                grad.addColorStop(j * diff, RGraph.trim(parts[j]));
            }
        }

        return grad ? grad : color;
    }



    /**
    * The function that draws the Y axis
    */
    RGraph.Drawing.YAxis.prototype.DrawYAxis = function ()
    {
        var ca   = this.canvas;
        var co   = this.context;
        var prop = this.properties;

        /**
        * Allow both axis.xxx and chart.xxx to prevent any confusion that may arise
        */
        for (i in prop) {
            if (typeof(i) == 'string') {
                var key = i.replace(/^chart\./, 'axis.');
                
                prop[key] = prop[i];
            }
        }

        var x               = this.x;
        var y               = this.gutterTop;
        var height          = ca.height - this.gutterBottom - this.gutterTop;
        var min             = prop['chart.min'] ? prop['chart.min'] : 0;
        var max             = prop['chart.max'];
        var title           = prop['chart.title'] ? prop['chart.title'] : '';
        var color           = prop['chart.colors'] ? prop['chart.colors'][0] : 'black';
        var title_color     = prop['chart.title.color'] ? prop['chart.title.color'] : color;
        var label_color     = prop['chart.text.color'] ? prop['chart.text.color'] : color;
        var numticks        = typeof(prop['chart.numticks']) == 'number' ? prop['chart.numticks'] : 10;
        var numlabels       = prop['chart.numlabels'] ? prop['chart.numlabels'] : 5;
        var font            = prop['chart.text.font'] ? prop['chart.text.font'] : 'Arial';
        var size            = prop['chart.text.size'] ? prop['chart.text.size'] : 10;
        var align           = typeof(prop['chart.align']) == 'string'? prop['chart.align'] : 'left';
        var formatter       = prop['chart.scale.formatter'];
        var decimals        = prop['chart.scale.decimals'];
        var invert          = prop['chart.scale.invert'];
        var scale_visible   = prop['chart.scale.visible'];
        var units_pre       = prop['chart.units.pre'];
        var units_post      = prop['chart.units.post'];
        var linewidth       = prop['chart.linewidth'] ? prop['chart.linewidth'] : 1;
        var notopendtick    = prop['chart.noendtick.top'];
        var nobottomendtick = prop['chart.noendtick.bottom'];
        var noyaxis         = prop['chart.noyaxis'];
        var xaxispos        = prop['chart.xaxispos'];


        // This fixes missing corner pixels in Chrome
        co.lineWidth = linewidth + 0.001;


        /**
        * Set the color
        */
        co.strokeStyle = color;

        if (!noyaxis) {
            /**
            * Draw the main vertical line
            */
            co.beginPath();
            co.moveTo(Math.round(x), y);
            co.lineTo(Math.round(x), y + height);
            co.stroke();

            /**
            * Draw the axes tickmarks
            */
            if (numticks) {
                
                var gap = (xaxispos == 'center' ? height / 2 : height) / numticks;
                var halfheight = height / 2;
    
                co.beginPath();
                    for (var i=(notopendtick ? 1 : 0); i<=(numticks - (nobottomendtick || xaxispos == 'center'? 1 : 0)); ++i) {
                        co.moveTo(align == 'right' ? x + 3 : x - 3, Math.round(y + (gap *i)));
                        co.lineTo(x, Math.round(y + (gap *i)));
                    }
                    
                    // Draw the bottom halves ticks if the X axis is in the center
                   if (xaxispos == 'center') {
                        for (var i=1; i<=numticks; ++i) {
                            co.moveTo(align == 'right' ? x + 3 : x - 3, Math.round(y + halfheight + (gap *i)));
                            co.lineTo(x, Math.round(y + halfheight + (gap *i)));
                        }
                    }
                co.stroke();
            }
        }


        /**
        * Draw the scale for the axes
        */
        co.fillStyle = label_color;
        co.beginPath();
        var text_len = 0;
            if (scale_visible) {
                for (var i=0; i<=numlabels; ++i) {
    
                    var original = ((max - min) * ((numlabels-i) / numlabels)) + min;
                
                    if (original == 0 && prop['chart.scale.zerostart'] == false) {
                        continue;
                    }
    
                    var text     = RGraph.number_format(this, original.toFixed(decimals), units_pre, units_post);
                    var text     = String(typeof(formatter) == 'function' ? formatter(this, original) : text);
                    var text_len = Math.max(text_len, this.context.measureText(text).width);
    
                    if (invert) {
                        var y = height - ((height / numlabels)*i);
                    } else {
                        var y = (height / numlabels)*i;
                    }
                    
                    if (prop['chart.xaxispos'] == 'center') {
                        y = y / 2;
                    }
    
    
                    /**
                    * Now - draw the labels
                    */
                    RGraph.Text2(this, {'font':font,
                                        'size':size,
                                        'x':x - (align == 'right' ? -5 : 5),
                                        'y':y + this.gutterTop,
                                        'text':text,
                                        'valign':'center',
                                        'halign':align == 'right' ? 'left' : 'right',
                                        'tag': 'scale'
                                       });
    
    
    
                    /**
                    * Draw the bottom half of the labels if the X axis is in the center
                    */
                    if (prop['chart.xaxispos'] == 'center' && i < numlabels) {
                        RGraph.Text2(this, {'font':font,
                                            'size':size,
                                            'x':x - (align == 'right' ? -5 : 5),
                                            'y':this.canvas.height - this.gutterBottom - y,
                                            'text':'-' + text,
                                            'valign':'center',
                                            'halign':align == 'right' ? 'left' : 'right',
                                            'tag': 'scale'
                                           });
                    }
                }
            }
        co.stroke();

        /**
        * Draw the title for the axes
        */
        if (title) {
            co.beginPath();

                co.fillStyle = title_color;
                var width = this.context.measureText(prop['chart.max']).width;

                RGraph.Text2(this, {'font':font,
                                    'size':size + 2,
                                    'x':align == 'right' ? x + width + 7 : x - width - 7,
                                    'y':height / 2 + this.gutterTop,
                                    'text':title,
                                    'valign':'bottom',
                                    'halign':'center',
                                    'angle':align == 'right' ? 90 : -90});
            co.stroke();
        }
    }
    
    
    /**
    * This detemines the maximum text width of either the scale or text
    * labels - whichever is given
    * 
    * @return number The maximum text width
    */
    RGraph.Drawing.YAxis.prototype.getWidth = function ()
    {
        var width = this.context.measureText(this.properties['chart.max']).width
        
        // Add the title width if it's specified
        if (this.properties['chart.title'] && this.properties['chart.title'].length) {
            width += (this.properties['chart.text.size'] * 1.5);
        }
        
        this.width = width;
        
        return width;
    }