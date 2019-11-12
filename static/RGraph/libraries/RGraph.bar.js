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
    
    if (typeof(RGraph) == 'undefined') RGraph = {};

    /**
    * The bar chart constructor
    * 
    * @param object canvas The canvas object
    * @param array  data   The chart data
    */
    RGraph.Bar = function (id, data)
    {
        // Get the canvas and context objects
        this.id                = id;
        this.canvas            = document.getElementById(id);
        this.context           = this.canvas.getContext ? this.canvas.getContext("2d") : null;
        this.canvas.__object__ = this;
        this.type              = 'bar';
        this.max               = 0;
        this.stackedOrGrouped  = false;
        this.isRGraph          = true;
        this.uid               = RGraph.CreateUID();
        this.canvas.uid        = this.canvas.uid ? this.canvas.uid : RGraph.CreateUID();
        this.colorsParsed      = false;


        /**
        * Compatibility with older browsers
        */
        RGraph.OldBrowserCompat(this.context);


        // Various config type stuff
        this.properties = {
            'chart.background.barcolor1':   'rgba(0,0,0,0)',
            'chart.background.barcolor2':   'rgba(0,0,0,0)',
            'chart.background.grid':        true,
            'chart.background.grid.color':  '#ddd',
            'chart.background.grid.width':  1,
            'chart.background.grid.hsize':  20,
            'chart.background.grid.vsize':  20,
            'chart.background.grid.vlines': true,
            'chart.background.grid.hlines': true,
            'chart.background.grid.border': true,
            'chart.background.grid.autofit':true,
            'chart.background.grid.autofit.numhlines': 5,
            'chart.background.grid.autofit.numvlines': 20,
            'chart.background.image.stretch': true,
            'chart.background.image.x':     null,
            'chart.background.image.y':     null,
            'chart.background.image.w':     null,
            'chart.background.image.h':     null,
            'chart.background.image.align': null,
            'chart.ytickgap':               20,
            'chart.smallyticks':            3,
            'chart.largeyticks':            5,
            'chart.numyticks':              10,
            'chart.hmargin':                5,
            'chart.hmargin.grouped':        1,
            'chart.strokecolor':            'rgba(0,0,0,0)',
            'chart.axis.color':             'black',
            'chart.axis.linewidth':         1,
            'chart.gutter.top':             25,
            'chart.gutter.bottom':          25,
            'chart.gutter.left':            25,
            'chart.gutter.right':           25,
            'chart.labels':                 null,
            'chart.labels.ingraph':         null,
            'chart.labels.above':           false,
            'chart.labels.above.decimals':  0,
            'chart.labels.above.size':      null,
            'chart.labels.above.angle':     null,
            'chart.ylabels':                true,
            'chart.ylabels.count':          5,
            'chart.ylabels.inside':         false,
            'chart.xlabels.offset':         0,
            'chart.xaxispos':               'bottom',
            'chart.yaxispos':               'left',
            'chart.text.angle':             0,
            'chart.text.color':             'black', // Gradients aren't supported for this color
            'chart.text.size':              10,
            'chart.text.font':              'Arial',
            'chart.ymin':                   0,
            'chart.ymax':                   null,
            'chart.title':                  '',
            'chart.title.font':             null,
            'chart.title.background':       null, // Gradients aren't supported for this color
            'chart.title.hpos':             null,
            'chart.title.vpos':             null,
            'chart.title.bold':             true,
            'chart.title.xaxis':            '',
            'chart.title.xaxis.bold':       true,
            'chart.title.xaxis.size':       null,
            'chart.title.xaxis.font':       null,
            'chart.title.yaxis':            '',
            'chart.title.yaxis.bold':       true,
            'chart.title.yaxis.size':       null,
            'chart.title.yaxis.font':       null,
            'chart.title.yaxis.color':      null, // Gradients aren't supported for this color
            'chart.title.xaxis.pos':        null,
            'chart.title.yaxis.pos':        null,
            'chart.title.x':                null,
            'chart.title.y':                null,
            'chart.title.halign':           null,
            'chart.title.valign':           null,            
            'chart.colors':                 ['#01B4FF', '#0f0', '#00f', '#ff0', '#0ff', '#0f0'],
            'chart.colors.sequential':      false,
            'chart.colors.reverse':         false,
            'chart.grouping':               'grouped',
            'chart.variant':                'bar',
            'chart.variant.sketch.verticals': true,
            'chart.shadow':                 false,
            'chart.shadow.color':           '#999',  // Gradients aren't supported for this color
            'chart.shadow.offsetx':         3,
            'chart.shadow.offsety':         3,
            'chart.shadow.blur':            3,
            'chart.tooltips':               null,
            'chart.tooltips.effect':        'fade',
            'chart.tooltips.css.class':     'RGraph_tooltip',
            'chart.tooltips.event':         'onclick',
            'chart.tooltips.highlight':     true,
            'chart.highlight.stroke':       'rgba(0,0,0,0)',
            'chart.highlight.fill':         'rgba(255,255,255,0.7)',
            'chart.background.hbars':       null,
            'chart.key':                    null,
            'chart.key.background':         'white',
            'chart.key.position':           'graph',
            'chart.key.shadow':             false,
            'chart.key.shadow.color':       '#666',
            'chart.key.shadow.blur':        3,
            'chart.key.shadow.offsetx':     2,
            'chart.key.shadow.offsety':     2,
            'chart.key.position.gutter.boxed': true,
            'chart.key.position.x':         null,
            'chart.key.position.y':         null,
            'chart.key.halign':             'right',
            'chart.key.color.shape':        'square',
            'chart.key.rounded':            true,
            'chart.key.text.size':          10,
            'chart.key.linewidth':          1,
            'chart.key.colors':             null,
            'chart.contextmenu':            null,
            'chart.units.pre':              '',
            'chart.units.post':             '',
            'chart.scale.decimals':         0,
            'chart.scale.point':            '.',
            'chart.scale.thousand':         ',',
            'chart.crosshairs':             false,
            'chart.crosshairs.color':       '#333',
            'chart.crosshairs.hline':       true,
            'chart.crosshairs.vline':       true,
            'chart.linewidth':              1,
            'chart.annotatable':            false,
            'chart.annotate.color':         'black',
            'chart.zoom.factor':            1.5,
            'chart.zoom.fade.in':           true,
            'chart.zoom.fade.out':          true,
            'chart.zoom.hdir':              'right',
            'chart.zoom.vdir':              'down',
            'chart.zoom.frames':            25,
            'chart.zoom.delay':             16.666,
            'chart.zoom.shadow':            true,
            'chart.zoom.background':        true,
            'chart.resizable':              false,
            'chart.resize.handle.adjust':   [0,0],
            'chart.resize.handle.background': null,
            'chart.adjustable':             false,
            'chart.noaxes':                 false,
            'chart.noxaxis':                false,
            'chart.noyaxis':                false,
            'chart.events.click':           null,
            'chart.events.mousemove':       null,
            'chart.numxticks':              null,
            'chart.bevel':                  false
        }

        // Check for support
        if (!this.canvas) {
            alert('[BAR] No canvas support');
            return;
        }

        /**
        * Determine whether the chart will contain stacked or grouped bars
        */
        for (var i=0; i<data.length; ++i) {
            if (typeof(data[i]) == 'object') {
                this.stackedOrGrouped = true;
            }
        }


        /**
        * Create the dollar objects so that functions can be added to them
        */
        var linear_data = RGraph.array_linearize(data);
        for (var i=0; i<linear_data.length; ++i) {
            this['$' + i] = {};
        }


        // Store the data
        this.data = data;
        
        // Used to store the coords of the bars
        this.coords     = [];
        this.coords2    = [];
        this.coordsText = [];



        /**
        * This linearises the data. Doing so can make it easier to pull
        * out the appropriate data from tooltips
        */
        this.data_arr = RGraph.array_linearize(this.data);


        /**
        * Translate half a pixel for antialiasing purposes - but only if it hasn't beeen
        * done already
        */
        if (!this.canvas.__rgraph_aa_translated__) {
            this.context.translate(0.5,0.5);

            this.canvas.__rgraph_aa_translated__ = true;
        }
        

        /**
        * Register the object
        */
        RGraph.Register(this);
    }



    /**
    * A setter
    * 
    * @param name  string The name of the property to set
    * @param value mixed  The value of the property
    */
    RGraph.Bar.prototype.Set = function (name, value)
    {
        name = name.toLowerCase();
        
        /**
        * This should be done first - prepend the propertyy name with "chart." if necessary
        */
        if (name.substr(0,6) != 'chart.') {
            name = 'chart.' + name;
        }

        if (name == 'chart.labels.abovebar') {
            name = 'chart.labels.above';
        }
        
        if (name == 'chart.strokestyle') {
            name = 'chart.strokecolor';
        }
        
        /**
        * Check for xaxispos
        */
        if (name == 'chart.xaxispos' ) {
            if (value != 'bottom' && value != 'center' && value != 'top') {
                alert('[BAR] (' + this.id + ') chart.xaxispos should be top, center or bottom. Tried to set it to: ' + value + ' Changing it to center');
                value = 'center';
            }
            
            if (value == 'top') {
                for (var i=0; i<this.data.length; ++i) {
                    if (typeof(this.data[i]) == 'number' && this.data[i] > 0) {
                        alert('[BAR] The data element with index ' + i + ' should be negative');
                    }
                }
            }
        }
        
        /**
        * lineWidth doesn't appear to like a zero setting
        */
        if (name.toLowerCase() == 'chart.linewidth' && value == 0) {
            value = 0.0001;
        }

        this.properties[name] = value;

        return this;
    }


    /**
    * A getter
    * 
    * @param name  string The name of the property to get
    */
    RGraph.Bar.prototype.Get = function (name)
    {
        /**
        * This should be done first - prepend the property name with "chart." if necessary
        */
        if (name.substr(0,6) != 'chart.') {
            name = 'chart.' + name;
        }

        return this.properties[name];
    }



    /**
    * The function you call to draw the bar chart
    */
    RGraph.Bar.prototype.Draw = function ()
    {

        // MUST be the first thing done!
        if (typeof(this.properties['chart.background.image']) == 'string') {
            RGraph.DrawBackgroundImage(this);
        }

        /**
        * Fire the onbeforedraw event
        */
        RGraph.FireCustomEvent(this, 'onbeforedraw');



        /**
        * Parse the colors. This allows for simple gradient syntax
        */
        if (!this.colorsParsed) {
            this.parseColors();
            
            // Don't want to do this again
            this.colorsParsed = true;
        }


        
        /**
        * This is new in May 2011 and facilitates indiviual gutter settings,
        * eg chart.gutter.left
        */
        this.gutterLeft   = this.properties['chart.gutter.left'];
        this.gutterRight  = this.properties['chart.gutter.right'];
        this.gutterTop    = this.properties['chart.gutter.top'];
        this.gutterBottom = this.properties['chart.gutter.bottom'];

        /**
        * Convert any null values to 0. Won't make any difference to the bar (as opposed to the line chart)
        */
        for (var i=0; i<this.data.length; ++i) {
            if (this.data[i] == null) {
                this.data[i] = 0;
            }
        }


        // Cache this in a class variable as it's used rather a lot

        /**
        * Check for tooltips and alert the user that they're not supported with pyramid charts
        */
        if (   (this.properties['chart.variant'] == 'pyramid' || this.properties['chart.variant'] == 'dot')
            && typeof(this.properties['chart.tooltips']) == 'object'
            && this.properties['chart.tooltips']
            && this.properties['chart.tooltips'].length > 0) {

            alert('[BAR] (' + this.id + ') Sorry, tooltips are not supported with dot or pyramid charts');
        }

        /**
        * Stop the coords arrays from growing uncontrollably
        */
        this.coords     = [];
        this.coords2    = [];
        this.coordsText = [];

        /**
        * Work out a few things. They need to be here because they depend on things you can change before you
        * call Draw() but after you instantiate the object
        */
        this.max            = 0;
        this.grapharea      = this.canvas.height - this.gutterTop - this.gutterBottom;
        this.halfgrapharea  = this.grapharea / 2;
        this.halfTextHeight = this.properties['chart.text.size'] / 2;


        // Progressively Draw the chart
        RGraph.background.Draw(this);




        //If it's a sketch chart variant, draw the axes first
        if (this.properties['chart.variant'] == 'sketch') {
            this.DrawAxes();
            this.Drawbars();
        } else {
            this.Drawbars();
            this.DrawAxes();
        }

        this.DrawLabels();
        
        
        /**
        * Draw the bevel if required
        */
        if (this.properties['chart.bevel'] || this.properties['chart.bevelled']) {
            this.DrawBevel();
        }


        // Draw the key if necessary
        if (this.properties['chart.key'] && this.properties['chart.key'].length) {
            RGraph.DrawKey(this, this.properties['chart.key'], this.properties['chart.colors']);
        }
        
        
        /**
        * Setup the context menu if required
        */
        if (this.properties['chart.contextmenu']) {
            RGraph.ShowContext(this);
        }


        /**
        * Is a line is defined, draw it
        *
        var line = this.Get('chart.line');

        if (line) {
        
            line.__bar__ = this;
            
            // Check the X axis positions
            if (this.Get('chart.xaxispos') != line.Get('chart.xaxispos')) {
                alert("[BAR] Using different X axis positions when combining the Bar and Line is not advised");
            }

            line.Set('chart.gutter.left',   this.Get('chart.gutter.left'));
            line.Set('chart.gutter.right',  this.Get('chart.gutter.right'));
            line.Set('chart.gutter.top',    this.Get('chart.gutter.top'));
            line.Set('chart.gutter.bottom', this.Get('chart.gutter.bottom'));

            line.Set('chart.hmargin', (this.canvas.width - this.gutterLeft - this.gutterRight) / (line.original_data[0].length * 2));
            
            // If a BAR custom yMax is set, use that
            if (this.Get('chart.ymax') && !line.Get('chart.ymax')) {
                line.Set('chart.ymax', this.Get('chart.ymax'));
            
            } else if (line.Get('chart.ymax')) {
                line.Set('chart.ymax', line.Get('chart.ymax'));
            }

            // The boolean is used to specify that the Line chart .Draw() method is being called by the Bar chart
            line.Draw(true);
        }
*/


        /**
        * Draw "in graph" labels
        */
        if (this.properties['chart.labels.ingraph']) {
            RGraph.DrawInGraphLabels(this);
        }

        
        /**
        * This function enables resizing
        */
        if (this.properties['chart.resizable']) {
            RGraph.AllowResizing(this);
        }


        /**
        * This installs the event listeners
        */
        RGraph.InstallEventListeners(this);


        /**
        * Fire the RGraph ondraw event
        */
        RGraph.FireCustomEvent(this, 'ondraw');
        
        return this;
    }



    /**
    * Draws the charts axes
    */
    RGraph.Bar.prototype.DrawAxes = function ()
    {
        if (this.properties['chart.noaxes']) {
            return;
        }

        var xaxispos = this.properties['chart.xaxispos'];
        var yaxispos = this.properties['chart.yaxispos'];
        var isSketch = this.properties['chart.variant'] == 'sketch';

        this.context.beginPath();
        this.context.strokeStyle = this.properties['chart.axis.color'];
        this.context.lineWidth   = this.properties['chart.axis.linewidth'] + 0.001;


        if (navigator.userAgent.indexOf('Safari') == -1) {
            this.context.lineCap = 'square';
        }


        // Draw the Y axis
        if (this.properties['chart.noyaxis'] == false) {
            if (yaxispos == 'right') {
                this.context.moveTo(this.canvas.width - this.gutterRight + (isSketch ? 3 : 0), this.gutterTop - (isSketch ? 3 : 0));
                this.context.lineTo(this.canvas.width - this.gutterRight - (isSketch ? 2 : 0), this.canvas.height - this.gutterBottom + (isSketch ? 5 : 0));
            } else {
                this.context.moveTo(this.gutterLeft - (isSketch ? 2 : 0), this.gutterTop - (isSketch ? 5 : 0));
                this.context.lineTo(this.gutterLeft - (isSketch ? 1 : 0), this.canvas.height - this.gutterBottom + (isSketch ? 5 : 0));
            }
        }
        
        // Draw the X axis
        if (this.properties['chart.noxaxis'] == false) {
            if (xaxispos == 'center') {
                this.context.moveTo(this.gutterLeft - (isSketch ? 5 : 0), Math.round(((this.canvas.height - this.gutterTop - this.gutterBottom) / 2) + this.gutterTop + (isSketch ? 2 : 0)));
                this.context.lineTo(this.canvas.width - this.gutterRight + (isSketch ? 5 : 0), Math.round(((this.canvas.height - this.gutterTop - this.gutterBottom) / 2) + this.gutterTop - (isSketch ? 2 : 0)));
            } else if (xaxispos == 'top') {
                this.context.moveTo(this.gutterLeft - (isSketch ? 3 : 0), this.gutterTop - (isSketch ? 3 : 0));
                this.context.lineTo(this.canvas.width - this.gutterRight + (isSketch ? 5 : 0), this.gutterTop + (isSketch ? 2 : 0));
            } else {
                this.context.moveTo(this.gutterLeft - (isSketch ? 5 : 0), this.canvas.height - this.gutterBottom - (isSketch ? 2 : 0));
                this.context.lineTo(this.canvas.width - this.gutterRight + (isSketch ? 8 : 0), this.canvas.height - this.gutterBottom + (isSketch ? 2 : 0));
            }
        }

        var numYTicks = this.properties['chart.numyticks'];

        // Draw the Y tickmarks
        if (this.properties['chart.noyaxis'] == false && !isSketch) {
            var yTickGap = (this.canvas.height - this.gutterTop - this.gutterBottom) / numYTicks;
            var xpos     = yaxispos == 'left' ? this.gutterLeft : this.canvas.width - this.gutterRight;

            if (this.properties['chart.numyticks'] > 0) {
                for (y=this.gutterTop;
                     xaxispos == 'center' ? y <= (this.canvas.height - this.gutterBottom) : y < (this.canvas.height - this.gutterBottom + (xaxispos == 'top' ? 1 : 0));
                     y += yTickGap) {

                    if (xaxispos == 'center' && y == (this.gutterTop + (this.grapharea / 2))) continue;
                    
                    // X axis at the top
                    if (xaxispos == 'top' && y == this.gutterTop) continue;

                    this.context.moveTo(xpos + (yaxispos == 'left' ? 0 : 0), Math.round(y));
                    this.context.lineTo(xpos + (yaxispos == 'left' ? -3 : 3), Math.round(y));
                }
            }

            /**
            * If the X axis is not being shown, draw an extra tick
            */
            if (this.properties['chart.noxaxis']) {
                if (xaxispos == 'center') {
                    this.context.moveTo(xpos + (yaxispos == 'left' ? -3 : 3), Math.round(this.canvas.height / 2));
                    this.context.lineTo(xpos, Math.round(this.canvas.height / 2));
                } else if (xaxispos == 'top') {
                    this.context.moveTo(xpos + (yaxispos == 'left' ? -3 : 3), Math.round(this.gutterTop));
                    this.context.lineTo(xpos, Math.round(this.gutterTop));
                } else {
                    this.context.moveTo(xpos + (yaxispos == 'left' ? -3 : 3), Math.round(this.canvas.height - this.gutterBottom));
                    this.context.lineTo(xpos, Math.round(this.canvas.height - this.gutterBottom));
                }
            }
        }


        // Draw the X tickmarks
        if (this.properties['chart.noxaxis'] == false && !isSketch) {

            if (typeof(this.properties['chart.numxticks']) == 'number') {
                var xTickGap = (this.canvas.width - this.gutterLeft - this.gutterRight) / this.properties['chart.numxticks'];
            } else {
                var xTickGap = (this.canvas.width - this.gutterLeft - this.gutterRight) / this.data.length;
            }

            if (xaxispos == 'bottom') {
                yStart   = this.canvas.height - this.gutterBottom;
                yEnd     = (this.canvas.height - this.gutterBottom) + 3;
            } else if (xaxispos == 'top') {
                yStart = this.gutterTop - 3;
                yEnd   = this.gutterTop;
            } else if (xaxispos == 'center') {
                yStart = ((this.canvas.height - this.gutterTop - this.gutterBottom) / 2) + this.gutterTop + 3;
                yEnd   = ((this.canvas.height - this.gutterTop - this.gutterBottom) / 2) + this.gutterTop - 3;
            }
            
            yStart = yStart;
            yEnd = yEnd;
            
            //////////////// X TICKS ////////////////
            var noEndXTick = this.properties['chart.noendxtick'];

            for (x=this.gutterLeft + (yaxispos == 'left' ? xTickGap : 0); x<this.canvas.width - this.gutterRight + (yaxispos == 'left' ? 5 : 0); x+=xTickGap) {

                if (yaxispos == 'left' && !noEndXTick && x > this.gutterLeft) {
                    this.context.moveTo(Math.round(x), yStart);
                    this.context.lineTo(Math.round(x), yEnd);
                
                } else if (yaxispos == 'left' && noEndXTick && x > this.gutterLeft && x < (this.canvas.width - this.gutterRight) ) {
                    this.context.moveTo(Math.round(x), yStart);
                    this.context.lineTo(Math.round(x), yEnd);
                
                } else if (yaxispos == 'right' && x < (this.canvas.width - this.gutterRight) && !noEndXTick) {
                    this.context.moveTo(Math.round(x), yStart);
                    this.context.lineTo(Math.round(x), yEnd);
                
                } else if (yaxispos == 'right' && x < (this.canvas.width - this.gutterRight) && x > (this.gutterLeft) && noEndXTick) {
                    this.context.moveTo(Math.round(x), yStart);
                    this.context.lineTo(Math.round(x), yEnd);
                }
            }
            
            if (this.properties['chart.noyaxis'] || this.properties['chart.numxticks'] == null) {
                if (typeof(this.properties['chart.numxticks']) == 'number' && this.properties['chart.numxticks'] > 0) {
                    this.context.moveTo(Math.round(this.gutterLeft), yStart);
                    this.context.lineTo(Math.round(this.gutterLeft), yEnd);
                }
            }
    
            //////////////// X TICKS ////////////////
        }

        /**
        * If the Y axis is not being shown, draw an extra tick
        */
        if (this.properties['chart.noyaxis'] && this.properties['chart.noxaxis'] == false && this.properties['chart.numxticks'] == null) {
            if (xaxispos == 'center') {
                this.context.moveTo(Math.round(this.gutterLeft), (this.canvas.height / 2) - 3);
                this.context.lineTo(Math.round(this.gutterLeft), (this.canvas.height / 2) + 3);
            } else {
                this.context.moveTo(Math.round(this.gutterLeft), this.canvas.height - this.gutterBottom);
                this.context.lineTo(Math.round(this.gutterLeft), this.canvas.height - this.gutterBottom + 3);
            }
        }

        this.context.stroke();
    }


    /**
    * Draws the bars
    */
    RGraph.Bar.prototype.Drawbars = function ()
    {
        // Variable "caching" so the context can be accessed as a local variable
        var ca   = this.canvas;
        var co   = this.context;
        var prop = this.properties;

        co.lineWidth   = prop['chart.linewidth'];
        co.strokeStyle = prop['chart.strokecolor'];
        co.fillStyle   = prop['chart.colors'][0];
        var prevX      = 0;
        var prevY      = 0;
        var decimals   = prop['chart.scale.decimals'];

        /**
        * Work out the max value
        */
        if (prop['chart.ymax']) {

            this.scale2 = RGraph.getScale2(this, {
                                                'max':prop['chart.ymax'],
                                                'strict': true,
                                                'min':prop['chart.ymin'],
                                                'scale.thousand':prop['chart.scale.thousand'],
                                                'scale.point':prop['chart.scale.point'],
                                                'scale.decimals':prop['chart.scale.decimals'],
                                                'ylabels.count':prop['chart.ylabels.count'],
                                                'scale.round':prop['chart.scale.round'],
                                                'units.pre': prop['chart.units.pre'],
                                                'units.post': prop['chart.units.post']
                                               });

        } else {

            for (i=0; i<this.data.length; ++i) {
                if (typeof(this.data[i]) == 'object') {
                    var value = prop['chart.grouping'] == 'grouped' ? Number(RGraph.array_max(this.data[i], true)) : Number(RGraph.array_sum(this.data[i])) ;

                } else {
                    var value = Number(this.data[i]);
                }

                this.max = Math.max(Math.abs(this.max), Math.abs(value));
            }

            this.scale2 = RGraph.getScale2(this, {
                                                'max':this.max,
                                                'min':prop['chart.ymin'],
                                                'scale.thousand':prop['chart.scale.thousand'],
                                                'scale.point':prop['chart.scale.point'],
                                                'scale.decimals':prop['chart.scale.decimals'],
                                                'ylabels.count':prop['chart.ylabels.count'],
                                                'scale.round':prop['chart.scale.round'],
                                                'units.pre': prop['chart.units.pre'],
                                                'units.post': prop['chart.units.post']
                                               });

        }
        /**
        * if the chart is adjustable fix the scale so that it doesn't change.
        */
        if (prop['chart.adjustable'] && !prop['chart.ymax']) {
            this.Set('chart.ymax', this.scale2.max);
        }

        /**
        * Draw horizontal bars here
        */
        if (prop['chart.background.hbars'] && prop['chart.background.hbars'].length > 0) {
            RGraph.DrawBars(this);
        }

        var variant = prop['chart.variant'];
        
        /**
        * Draw the 3D axes is necessary
        */
        if (variant == '3d') {
            RGraph.Draw3DAxes(this);
        }

        /**
        * Get the variant once, and draw the bars, be they regular, stacked or grouped
        */
        
        // Get these variables outside of the loop
        var xaxispos      = prop['chart.xaxispos'];
        var width         = (this.canvas.width - this.gutterLeft - this.gutterRight ) / this.data.length;
        var orig_height   = height;
        var hmargin       = prop['chart.hmargin'];
        var shadow        = prop['chart.shadow'];
        var shadowColor   = prop['chart.shadow.color'];
        var shadowBlur    = prop['chart.shadow.blur'];
        var shadowOffsetX = prop['chart.shadow.offsetx'];
        var shadowOffsetY = prop['chart.shadow.offsety'];
        var strokeStyle   = prop['chart.strokecolor'];
        var colors        = prop['chart.colors'];
        var sequentialColorIndex = 0;

        for (i=0; i<this.data.length; ++i) {

            // Work out the height
            //The width is up outside the loop
            var height = ((RGraph.array_sum(this.data[i]) < 0 ? RGraph.array_sum(this.data[i]) + this.scale2.min : RGraph.array_sum(this.data[i]) - this.scale2.min) / (this.scale2.max - this.scale2.min) ) * (ca.height - this.gutterTop - this.gutterBottom);

            // Half the height if the Y axis is at the center
            if (xaxispos == 'center') {
                height /= 2;
            }

            var x = (i * width) + this.gutterLeft;
            var y = xaxispos == 'center' ? ((ca.height - this.gutterTop - this.gutterBottom) / 2) + this.gutterTop - height
                                         : ca.height - height - this.gutterBottom;

            // xaxispos is top
            if (xaxispos == 'top') {
                y = this.gutterTop + Math.abs(height);
            }


            // Account for negative lengths - Some browsers (eg Chrome) don't like a negative value
            if (height < 0) {
                y += height;
                height = Math.abs(height);
            }

            /**
            * Turn on the shadow if need be
            */
            if (shadow) {
                co.shadowColor   = shadowColor;
                co.shadowBlur    = shadowBlur;
                co.shadowOffsetX = shadowOffsetX;
                co.shadowOffsetY = shadowOffsetY;
            }

            /**
            * Draw the bar
            */
            this.context.beginPath();
                if (typeof(this.data[i]) == 'number') {

                    var barWidth = width - (2 * hmargin);
                    
                    /**
                    * Check for a negative bar width
                    */
                    if (barWidth < 0) {
                        alert('[RGRAPH] Warning: you have a negative bar width. This may be caused by the chart.hmargin being too high or the width of the canvas not being sufficient.');
                    }

                    // Set the fill color
                    co.strokeStyle = strokeStyle;
                    co.fillStyle = colors[0];
                    
                    /**
                    * Sequential colors
                    */
                    if (prop['chart.colors.sequential']) {
                        co.fillStyle = colors[i];
                    }

                    if (variant == 'sketch') {

                        this.context.lineCap = 'round';
                        
                        var sketchOffset = 3;

                        co.beginPath();

                        co.strokeStyle = colors[0];

                        /**
                        * Sequential colors
                        */
                        if (prop['chart.colors.sequential']) {
                            co.strokeStyle = colors[i];
                        }

                        // Left side
                        co.moveTo(x + hmargin + 2, y + height - 2);
                        co.lineTo(x + hmargin -    1, y - 4);

                        // The top
                        co.moveTo(x + hmargin - 3, y + -2 + (this.data[i] < 0 ? height : 0));
                        co.bezierCurveTo(
                                         x + ((hmargin + width) * 0.33),
                                         y + 15 + (this.data[i] < 0 ? height - 10: 0),
                                         x + ((hmargin + width) * 0.66),
                                         y + 5 + (this.data[i] < 0 ? height - 10 : 0),x + hmargin + width + -1, y + 0 + (this.data[i] < 0 ? height : 0)
                                        );


                        // The right side
                        co.moveTo(x + hmargin + width - 5, y  - 5);
                        co.lineTo(x + hmargin + width - 3, y + height - 3);

                        if (prop['chart.variant.sketch.verticals']) {
                            for (var r=0.2; r<=0.8; r+=0.2) {
                                co.moveTo(x + hmargin + width + (r > 0.4 ? -1 : 3) - (r * width),y - 1);
                                co.lineTo(x + hmargin + width - (r > 0.4 ? 1 : -1) - (r * width), y + height + (r == 0.2 ? 1 : -2));
                            }
                        }

                        this.context.stroke();

                    // Regular bar
                    } else if (variant == 'bar' || variant == '3d' || variant == 'glass' || variant == 'bevel') {
                    
                        if (RGraph.isOld() && shadow) {
                            this.DrawIEShadow([x + hmargin, y, barWidth, height]);
                        }
                        
                        if (variant == 'glass') {
                            RGraph.filledCurvyRect(this.context, x + hmargin, y, barWidth, height, 3, this.data[i] > 0, this.data[i] > 0, this.data[i] < 0, this.data[i] < 0);
                            RGraph.strokedCurvyRect(this.context, x + hmargin, y, barWidth, height, 3, this.data[i] > 0, this.data[i] > 0, this.data[i] < 0, this.data[i] < 0);
                        } else {
                            this.context.strokeRect(x + hmargin, y, barWidth, height);
                            this.context.fillRect(x + hmargin, y, barWidth, height);
                        }

                        // 3D effect
                        if (variant == '3d') {

                            var prevStrokeStyle = co.strokeStyle;
                            var prevFillStyle   = co.fillStyle;

                            // Draw the top
                            co.beginPath();
                                co.moveTo(x + hmargin, y);
                                co.lineTo(x + hmargin + 10, y - 5);
                                co.lineTo(x + hmargin + 10 + barWidth, y - 5);
                                co.lineTo(x + hmargin + barWidth, y);
                            co.closePath();

                            co.stroke();
                            co.fill();

                            // Draw the right hand side
                            co.beginPath();
                                co.moveTo(x + hmargin + barWidth, y);
                                co.lineTo(x + hmargin + barWidth + 10, y - 5);
                                co.lineTo(x + hmargin + barWidth + 10, y + height - 5);
                                co.lineTo(x + hmargin + barWidth, y + height);
                            co.closePath();
    
                            co.stroke();                        
                            co.fill();

                            // Draw the darker top section
                            co.beginPath();                            
                                co.fillStyle = 'rgba(255,255,255,0.3)';
                                co.moveTo(x + hmargin, y);
                                co.lineTo(x + hmargin + 10, y - 5);
                                co.lineTo(x + hmargin + 10 + barWidth, y - 5);
                                co.lineTo(x + hmargin + barWidth, y);
                                co.lineTo(x + hmargin, y);
                            co.closePath();
    
                            co.stroke();
                            co.fill();

                            // Draw the darker right side section
                            co.beginPath();
                                co.fillStyle = 'rgba(0,0,0,0.4)';
                                co.moveTo(x + hmargin + barWidth, y);
                                co.lineTo(x + hmargin + barWidth + 10, y - 5);
                                co.lineTo(x + hmargin + barWidth + 10, y - 5 + height);
                                co.lineTo(x + hmargin + barWidth, y + height);
                                co.lineTo(x + hmargin + barWidth, y);
                            co.closePath();

                            co.stroke();
                            co.fill();

                            co.strokeStyle = prevStrokeStyle;
                            co.fillStyle   = prevFillStyle;
                        
                        // Glass variant
                        } else if (variant == 'glass') {
 
                            var grad = co.createLinearGradient(x + hmargin,y,x + hmargin + (barWidth / 2),y);
                            grad.addColorStop(0, 'rgba(255,255,255,0.9)');
                            grad.addColorStop(1, 'rgba(255,255,255,0.5)');

                            co.beginPath();
                            co.fillStyle = grad;
                            co.fillRect(x + hmargin + 2,y + (this.data[i] > 0 ? 2 : 0),(barWidth / 2) - 2,height - 2);
                            co.fill();
                        }

                        // This bit draws the text labels that appear above the bars if requested
                        if (prop['chart.labels.above']) {

                            // Turn off any shadow
                            if (shadow) {
                                RGraph.NoShadow(this);
                            }

                            var yPos = y - 3;
                            var xPos = x + hmargin + (barWidth / 2);

                            // Account for negative bars
                            if (this.data[i] < 0) {
                                yPos += height + 6 + (prop['chart.text.size']);
                            }

                            // Account for chart.xaxispos=top
                            if (prop['chart.xaxispos'] == 'top') {
                                yPos = this.gutterTop + height + 6 + (typeof(prop['chart.labels.above.size']) == 'number' ? prop['chart.labels.above.size'] : prop['chart.text.size'] - 4);
                            }

                            // Account for chart.variant=3d
                            if (prop['chart.variant'] == '3d') {
                                yPos -= 3;
                                xPos += 5;
                            }
                            
                            // Angled above labels
                            if (this.properties['chart.labels.above.angle']) {
                                var angle = -45;
                                var halign = 'left';
                                var valign = 'center';
                            } else {
                                var angle = 0;
                                var halign = 'center';
                                var valign = 'bottom';
                            }

                            co.fillStyle = prop['chart.text.color'];

                            RGraph.Text2(this, {'font': prop['chart.text.font'],
                                                'size': typeof(prop['chart.labels.above.size']) == 'number' ? prop['chart.labels.above.size'] : prop['chart.text.size'] - 3,
                                                   'x': xPos,
                                                   'y': yPos,
                                                'text': RGraph.number_format(this, Number(this.data[i]).toFixed(prop['chart.labels.above.decimals']),prop['chart.units.pre'],prop['chart.units.post']),
                                              'halign': halign,
                                              'marker': false,
                                              'valign': valign,
                                              'angle': angle,
                                              'tag': 'labels.above'
                                             });
                        }

                    // Dot chart
                    } else if (variant == 'dot') {

                        co.beginPath();
                        co.moveTo(x + (width / 2), y);
                        co.lineTo(x + (width / 2), y + height);
                        co.stroke();
                        
                        co.beginPath();
                        co.fillStyle = this.properties['chart.colors'][i];
                        co.arc(x + (width / 2), y + (this.data[i] > 0 ? 0 : height), 2, 0, 6.28, 0);
                        
                        // Set the colour for the dots
                        co.fillStyle = prop['chart.colors'][0];

                        /**
                        * Sequential colors
                        */
                        if (prop['chart.colors.sequential']) {
                            co.fillStyle = colors[i];
                        }

                        co.stroke();
                        co.fill();


                    // Unknown variant type
                    } else {
                        alert('[BAR] Warning! Unknown chart.variant: ' + variant);
                    }

                    this.coords.push([x + hmargin, y, width - (2 * hmargin), height]);

                        if (typeof this.coords2[i] == 'undefined') {
                            this.coords2[i] = [];
                        }
                        this.coords2[i].push([x + hmargin, y, width - (2 * hmargin), height]);


                /**
                * Stacked bar
                */
                } else if (typeof(this.data[i]) == 'object' && prop['chart.grouping'] == 'stacked') {
                
                    if (this.scale2.min) {
                        alert("[ERROR] Stacked Bar charts with a Y min are not supported");
                    }
                    
                    var barWidth     = width - (2 * hmargin);
                    var redrawCoords = [];// Necessary to draw if the shadow is enabled
                    var startY       = 0;
                    var dataset      = this.data[i];
                    
                    /**
                    * Check for a negative bar width
                    */
                    if (barWidth < 0) {
                        alert('[RGRAPH] Warning: you have a negative bar width. This may be caused by the chart.hmargin being too high or the width of the canvas not being sufficient.');
                    }

                    for (j=0; j<dataset.length; ++j) {

                        // Stacked bar chart and X axis pos in the middle - poitless since negative values are not permitted
                        if (xaxispos == 'center') {
                            alert("[BAR] It's pointless having the X axis position at the center on a stacked bar chart.");
                            return;
                        }

                        // Negative values not permitted for the stacked chart
                        if (this.data[i][j] < 0) {
                            alert('[BAR] Negative values are not permitted with a stacked bar chart. Try a grouped one instead.');
                            return;
                        }

                        /**
                        * Set the fill and stroke colors
                        */
                        co.strokeStyle = strokeStyle
                        co.fillStyle = colors[j];
    
                        if (prop['chart.colors.reverse']) {
                            co.fillStyle = colors[this.data[i].length - j - 1];
                        }
                        
                        if (prop['chart.colors.sequential'] && colors[sequentialColorIndex]) {
                            co.fillStyle = colors[sequentialColorIndex++];
                        } else if (prop['chart.colors.sequential']) {
                            co.fillStyle = colors[sequentialColorIndex - 1];
                        }

                        var height = (dataset[j] / this.scale2.max) * (ca.height - this.gutterTop - this.gutterBottom );

                        // If the X axis pos is in the center, we need to half the  height
                        if (xaxispos == 'center') {
                            height /= 2;
                        }

                        var totalHeight = (RGraph.array_sum(dataset) / this.scale2.max) * (ca.height - hmargin - this.gutterTop - this.gutterBottom);

                        /**
                        * Store the coords for tooltips
                        */
                        this.coords.push([x + hmargin, y, width - (2 * hmargin), height]);
                        if (typeof this.coords2[i] == 'undefined') {
                            this.coords2[i] = [];
                        }
                        this.coords2[i].push([x + hmargin, y, width - (2 * hmargin), height]);

                        // MSIE shadow
                        if (RGraph.isOld() && shadow) {
                            this.DrawIEShadow([x + hmargin, y, width - (2 * hmargin), height + 1]);
                        }

                        co.strokeRect(x + hmargin, y, width - (2 * hmargin), height);
                        co.fillRect(x + hmargin, y, width - (2 * hmargin), height);

                        
                        if (j == 0) {
                            var startY = y;
                            var startX = x;
                        }

                        /**
                        * Store the redraw coords if the shadow is enabled
                        */
                        if (shadow) {
                            redrawCoords.push([x + hmargin, y, width - (2 * hmargin), height, co.fillStyle]);
                        }

                        /**
                        * Stacked 3D effect
                        */
                        if (variant == '3d') {

                            var prevFillStyle = co.fillStyle;
                            var prevStrokeStyle = co.strokeStyle;

    
                            // Draw the top side
                            if (j == 0) {
                                co.beginPath();
                                    co.moveTo(startX + hmargin, y);
                                    co.lineTo(startX + 10 + hmargin, y - 5);
                                    co.lineTo(startX + 10 + barWidth + hmargin, y - 5);
                                    co.lineTo(startX + barWidth + hmargin, y);
                                co.closePath();
                                
                                co.fill();
                                co.stroke();
                            }

                            // Draw the side section
                            co.beginPath();
                                co.moveTo(startX + barWidth + hmargin, y);
                                co.lineTo(startX + barWidth + hmargin + 10, y - 5);
                                co.lineTo(startX + barWidth + hmargin + 10, y - 5 + height);
                                co.lineTo(startX + barWidth + hmargin , y + height);
                            co.closePath();
                            
                            co.fill();
                            co.stroke();

                            // Draw the darker top side
                            if (j == 0) {
                                co.fillStyle = 'rgba(255,255,255,0.3)';
                                co.beginPath();
                                    co.moveTo(startX + hmargin, y);
                                    co.lineTo(startX + 10 + hmargin, y - 5);
                                    co.lineTo(startX + 10 + barWidth + hmargin, y - 5);
                                    co.lineTo(startX + barWidth + hmargin, y);
                                co.closePath();
                                
                                co.fill();
                                co.stroke();
                            }

                            // Draw the darker side section
                            co.fillStyle = 'rgba(0,0,0,0.4)';
                            co.beginPath();
                                co.moveTo(startX + barWidth + hmargin, y);
                                co.lineTo(startX + barWidth + hmargin + 10, y - 5);
                                co.lineTo(startX + barWidth + hmargin + 10, y - 5 + height);
                                co.lineTo(startX + barWidth + hmargin , y + height);
                            co.closePath();
                            
                            co.fill();
                            co.stroke();

                            co.strokeStyle = prevStrokeStyle;
                            co.fillStyle = prevFillStyle;
                        }

                        y += height;
                    }

                    // This bit draws the text labels that appear above the bars if requested
                    if (this.Get('chart.labels.above')) {

                        // Turn off any shadow
                        RGraph.NoShadow(this);

                        co.fillStyle = prop['chart.text.color'];

                        // Angled above labels
                        if (this.properties['chart.labels.above.angle']) {
                            var angle = -45;
                            var halign = 'left';
                            var valign = 'center';
                        } else {
                            var angle = 0;
                            var halign = 'center';
                            var valign = 'bottom';
                        }

                        RGraph.Text2(this,{'font': prop['chart.text.font'],
                                           'size': typeof(prop['chart.labels.above.size']) == 'number' ? prop['chart.labels.above.size'] : prop['chart.text.size'] - 3,
                                           'x': startX + (barWidth / 2) + prop['chart.hmargin'],
                                           'y': startY - (prop['chart.shadow'] && this.properties['chart.shadow.offsety'] < 0 ? 7 : 4) - (prop['chart.variant'] == '3d' ? 5 : 0),
                                           'text': String(prop['chart.units.pre'] + RGraph.array_sum(this.data[i]).toFixed(prop['chart.labels.above.decimals']) + prop['chart.units.post']),
                                           'angle': angle,
                                           'valign': valign,
                                           'halign': halign,
                                            'tag': 'labels.above'
                                          });

                      
                        // Turn any shadow back on
                        if (shadow) {
                            co.shadowColor   = shadowColor;
                            co.shadowBlur    = shadowBlur;
                            co.shadowOffsetX = shadowOffsetX;
                            co.shadowOffsetY = shadowOffsetY;
                        }
                    }
                    

                    /**
                    * Redraw the bars if the shadow is enabled due to hem being drawn from the bottom up, and the
                    * shadow spilling over to higher up bars
                    */
                    if (shadow) {

                        RGraph.NoShadow(this);

                        for (k=0; k<redrawCoords.length; ++k) {
                            co.strokeStyle = strokeStyle;
                            co.fillStyle = redrawCoords[k][4];
                            co.strokeRect(redrawCoords[k][0], redrawCoords[k][1], redrawCoords[k][2], redrawCoords[k][3]);
                            co.fillRect(redrawCoords[k][0], redrawCoords[k][1], redrawCoords[k][2], redrawCoords[k][3]);

                            co.stroke();
                            co.fill();
                        }
                        
                        // Reset the redraw coords to be empty
                        redrawCoords = [];
                    }
                /**
                * Grouped bar
                */
                } else if (typeof(this.data[i]) == 'object' && this.properties['chart.grouping'] == 'grouped') {

                    var redrawCoords = [];
                    co.lineWidth = prop['chart.linewidth'];

                    for (j=0; j<this.data[i].length; ++j) {

                        // Set the fill and stroke colors
                        co.strokeStyle = strokeStyle;
                        co.fillStyle   = colors[j];
                        
                        /**
                        * Sequential colors
                        */
                        if (prop['chart.colors.sequential'] && colors[sequentialColorIndex]) {
                            co.fillStyle = colors[sequentialColorIndex++];
                        } else if (prop['chart.colors.sequential']) {
                            co.fillStyle = colors[sequentialColorIndex - 1];
                        }

                        var individualBarWidth = (width - (2 * hmargin)) / this.data[i].length;
                        var height = ((this.data[i][j] + (this.data[i][j] < 0 ? this.scale2.min : (-1 * this.scale2.min) )) / (this.scale2.max - this.scale2.min) ) * (ca.height - this.gutterTop - this.gutterBottom );
                        var groupedMargin = this.properties['chart.hmargin.grouped'];
                        var startX = x + hmargin + (j * individualBarWidth);

                        /**
                        * Check for a negative bar width
                        */
                        if (individualBarWidth < 0) {
                            alert('[RGRAPH] Warning: you have a negative bar width. This may be caused by the chart.hmargin being too high or the width of the canvas not being sufficient.');
                        }

                        // If the X axis pos is in the center, we need to half the  height
                        if (xaxispos == 'center') {
                            height /= 2;
                        }

                        /**
                        * Determine the start positioning for the bar
                        */
                        if (xaxispos == 'top') {
                            var startY = this.gutterTop;
                            var height = Math.abs(height);

                        } else if (xaxispos == 'center') {
                            var startY = this.gutterTop + (this.grapharea / 2) - height;

                        } else {
                            var startY = this.canvas.height - this.gutterBottom - height;
                            var height = Math.abs(height);
                        }

                        /**
                        * Draw MSIE shadow
                        */
                        if (RGraph.isOld() && shadow) {
                            this.DrawIEShadow([startX, startY, individualBarWidth, height]);
                        }

                        co.strokeRect(startX + groupedMargin, startY, individualBarWidth - (2 * groupedMargin), height);
                        co.fillRect(startX + groupedMargin, startY, individualBarWidth - (2 * groupedMargin), height);
                        y += height;



                        /**
                        * Grouped 3D effect
                        */
                        if (variant == '3d') {
                            var prevFillStyle = co.fillStyle;
                            var prevStrokeStyle = co.strokeStyle;
                            
                            // Draw the top side
                            co.beginPath();
                                co.moveTo(startX, startY);
                                co.lineTo(startX + 10, startY - 5);
                                co.lineTo(startX + 10 + individualBarWidth, startY - 5);
                                co.lineTo(startX + individualBarWidth, startY);
                            co.closePath();
                            
                            co.fill();
                            co.stroke();
                            
                            // Draw the side section
                            co.beginPath();
                                co.moveTo(startX + individualBarWidth, startY);
                                co.lineTo(startX + individualBarWidth + 10, startY - 5);
                                co.lineTo(startX + individualBarWidth + 10, startY - 5 + height);
                                co.lineTo(startX + individualBarWidth , startY + height);
                            co.closePath();
                            
                            co.fill();
                            co.stroke();


                            // Draw the darker top side
                            co.fillStyle = 'rgba(255,255,255,0.3)';
                            co.beginPath();
                                co.moveTo(startX, startY);
                                co.lineTo(startX + 10, startY - 5);
                                co.lineTo(startX + 10 + individualBarWidth, startY - 5);
                                co.lineTo(startX + individualBarWidth, startY);
                            co.closePath();
                            
                            co.fill();
                            co.stroke();
                            
                            // Draw the darker side section
                            co.fillStyle = 'rgba(0,0,0,0.4)';
                            co.beginPath();
                                co.moveTo(startX + individualBarWidth, startY);
                                co.lineTo(startX + individualBarWidth + 10, startY - 5);
                                co.lineTo(startX + individualBarWidth + 10, startY - 5 + height);
                                co.lineTo(startX + individualBarWidth , startY + height);
                            co.closePath();
                            
                            co.fill();
                            co.stroke();

                            co.strokeStyle = prevStrokeStyle;
                            co.fillStyle   = prevFillStyle;
                        }
                        
                        if (height < 0) {
                            height = Math.abs(height);
                            startY = startY - height;
                        }

                        this.coords.push([startX + groupedMargin, startY, individualBarWidth - (2 * groupedMargin), height]);
                        if (typeof this.coords2[i] == 'undefined') {
                            this.coords2[i] = [];
                        }
                        this.coords2[i].push([x + hmargin + groupedMargin, y, width - (2 * hmargin) - (2 * groupedMargin), height]);

                        // Facilitate shadows going to the left
                        if (prop['chart.shadow']) {
                            redrawCoords.push([startX + groupedMargin, startY, individualBarWidth - (2 * groupedMargin), height, co.fillStyle]);
                        }


                        // This bit draws the text labels that appear above the bars if requested
                        if (prop['chart.labels.above']) {

                            co.strokeStyle = 'rgba(0,0,0,0)';
                        
                            // Turn off any shadow
                            if (shadow) {
                                RGraph.NoShadow(this);
                            }
                        
                            var yPos = y - 3;

                            // Angled above labels
                            if (this.properties['chart.labels.above.angle']) {
                                var angle = -45;
                                var halign = 'left';
                                var valign = 'center';
                            } else {

                                var angle = 0;
                                var halign = 'center';
                                var valign = 'bottom';
                        
                                // Account for negative bars
                                if (this.data[i][j] < 0 || this.properties['chart.xaxispos'] == 'top') {
                                    yPos = startY + height + 6;
                                    var valign = 'top';
                                } else {
                                    yPos = startY;
                                }
                            }

                            co.fillStyle = prop['chart.text.color'];

                            RGraph.Text2(this, {'font': prop['chart.text.font'],
                                                'size': typeof(prop['chart.labels.above.size']) == 'number' ? prop['chart.labels.above.size'] : prop['chart.text.size'] - 3,
                                                'x': startX + (individualBarWidth / 2),
                                                'y': yPos - 3,
                                                'text': RGraph.number_format(this, this.data[i][j].toFixed(prop['chart.labels.above.decimals'])),
                                                'halign': halign,
                                                'valign': valign,
                                                'angle':angle,
                                                'tag': 'labels.above'
                                               });
                          
                            // Turn any shadow back on
                            if (shadow) {
                                co.shadowColor   = shadowColor;
                                co.shadowBlur    = shadowBlur;
                                co.shadowOffsetX = shadowOffsetX;
                                co.shadowOffsetY = shadowOffsetY;
                            }
                        }
                    }
                    
                    /**
                    * Redraw the bar if shadows are going to the left
                    */
                    if (redrawCoords.length) {

                        RGraph.NoShadow(this);
                        
                        co.lineWidth = prop['chart.linewidth'];

                        co.beginPath();
                            for (var j=0; j<redrawCoords.length; ++j) {

                                co.fillStyle   = redrawCoords[j][4];
                                co.strokeStyle = prop['chart.strokecolor'];

                                co.fillRect(redrawCoords[j][0], redrawCoords[j][1], redrawCoords[j][2], redrawCoords[j][3]);
                                co.strokeRect(redrawCoords[j][0], redrawCoords[j][1], redrawCoords[j][2], redrawCoords[j][3]);
                            }
                        co.fill();
                        co.stroke();

                        redrawCoords = [];
                    }
                }

            co.closePath();
        }

        /**
        * Turn off any shadow
        */
        RGraph.NoShadow(this);
    }



    /**
    * Draws the labels for the graph
    */
    RGraph.Bar.prototype.DrawLabels = function ()
    {
        var context    = this.context;
        var text_angle = this.properties['chart.text.angle'];
        var text_size  = this.properties['chart.text.size'];
        var labels     = this.properties['chart.labels'];


        // Draw the Y axis labels:
        if (this.properties['chart.ylabels']) {
            if (this.properties['chart.xaxispos'] == 'top')    this.Drawlabels_top();
            if (this.properties['chart.xaxispos'] == 'center') this.Drawlabels_center();
            if (this.properties['chart.xaxispos'] == 'bottom') this.Drawlabels_bottom();
        }

        /**
        * The X axis labels
        */
        if (typeof(labels) == 'object' && labels) {

            var yOffset = Number(this.properties['chart.xlabels.offset']);

            /**
            * Text angle
            */
            if (this.properties['chart.text.angle'] != 0) {
                var valign =  'center';
                var halign =  'right';
                var angle  = 0 - this.properties['chart.text.angle'];
            } else {
                var valign =  'top';
                var halign =  'center';
                var angle  = 0;
            }

            // Draw the X axis labels
            context.fillStyle = this.properties['chart.text.color'];
            
            // How wide is each bar
            var barWidth = (this.canvas.width - this.gutterRight - this.gutterLeft) / labels.length;
            
            // Reset the xTickGap
            xTickGap = (this.canvas.width - this.gutterRight - this.gutterLeft) / labels.length

            // Draw the X tickmarks
            var i=0;
            var font = this.properties['chart.text.font'];

            for (x=this.gutterLeft + (xTickGap / 2); x<=this.canvas.width - this.gutterRight; x+=xTickGap) {

                RGraph.Text2(this, {'font': font,
                                    'size': text_size,
                                       'x': x,
                                       'y': this.properties['chart.xaxispos'] == 'top' ? this.gutterTop - yOffset - 5: (this.canvas.height - this.gutterBottom) + yOffset + 3,
                                    'text': String(labels[i++]),
                                  'valign': this.properties['chart.xaxispos'] == 'top' ? 'bottom' : valign,
                                  'halign': halign,
                                    'tag':'label',
                                    'marker':false,
                                    'angle':angle,
                                    'tag': 'labels'
                                   });
            }
        }
        
        /**
        * If chart.labels.above.specific is specified, draw them
        */
        if (this.properties['chart.labels.above.specific']) {
        
            var labels = this.properties['chart.labels.above.specific'];
            
            for (var i=0; i<this.coords.length; ++i) {

                var xaxispos = this.properties['chart.xaxispos'];
                var coords = this.coords[i];
                var value  = this.data_arr[i];
                var valign =  (value >=0 && xaxispos != 'top') ? 'bottom' : 'top';
                var halign = 'center';
                var text   = labels[i];


                if (text && text.toString().length > 0) {
                    RGraph.Text2(this, {'font': this.properties['chart.text.font'],
                                        'size': this.properties['chart.labels.above.size'] ? this.properties['chart.labels.above.size'] : this.properties['chart.text.size'],
                                        'x': coords[0] + (coords[2] / 2),
                                        'y': (value >=0 && xaxispos != 'top') ? coords[1] - 5 : coords[1] + coords[3] + 3,
                                        'text': String(labels[i]),
                                        'valign': valign,
                                        'halign': halign,
                                        'tag': 'labels.above'
                                       });
                }
            }
        }
    }



    /**
    * Draws the X axis at the top
    */
    RGraph.Bar.prototype.Drawlabels_top = function ()
    {
        var ca   = this.canvas;
        var co   = this.context;
        var prop = this.properties;

        co.beginPath();
        co.fillStyle   = prop['chart.text.color'];
        co.strokeStyle = 'black';

        if (prop['chart.xaxispos'] == 'top') {

            var context    = co;
            var text_size  = prop['chart.text.size'];
            var units_pre  = prop['chart.units.pre'];
            var units_post = prop['chart.units.post'];
            var align      = prop['chart.yaxispos'] == 'left' ? 'right' : 'left';
            var font       = prop['chart.text.font'];
            var numYLabels = prop['chart.ylabels.count'];
            var ymin       = prop['chart.ymin'];

            if (prop['chart.ylabels.inside'] == true) {
                var xpos  = prop['chart.yaxispos'] == 'left' ? this.gutterLeft + 5 : ca.width - this.gutterRight - 5;
                var align = prop['chart.yaxispos'] == 'left' ? 'left' : 'right';
                var boxed = true;
            } else {
                var xpos  = prop['chart.yaxispos'] == 'left' ? this.gutterLeft - 5 : ca.width - this.gutterRight + 5;
                var boxed = false;
            }
            
            /**
            * Draw specific Y labels here so that the local variables can be reused
            */
            if (typeof(prop['chart.ylabels.specific']) == 'object' && prop['chart.ylabels.specific']) {
                
                var labels = RGraph.array_reverse(prop['chart.ylabels.specific']);
                var grapharea = ca.height - this.gutterTop - this.gutterBottom;

                for (var i=0; i<labels.length; ++i) {
                    
                    var y = this.gutterTop + (grapharea * (i / labels.length)) + (grapharea / labels.length);

                    RGraph.Text2(this, {'font': font,
                                        'size': text_size,
                                        'x': xpos,
                                        'y': y,
                                        'text': String(labels[i]),
                                        'valign': 'center',
                                        'halign': align,
                                        'bordered':boxed,
                                        'tag': 'scale'
                                       });
                }

                return;
            }







            /**
            * Draw the scale
            */
            var labels = this.scale2.labels;
            for (var i=0; i<labels.length; ++i) {
                RGraph.Text2(this, {'font': font,
                                    'size':text_size,
                                    'x':xpos,
                                    'y':this.gutterTop + ((this.grapharea / labels.length) * (i + 1)),
                                    'text': '-' + labels[i],
                                    'valign': 'center',
                                    'halign': align,
                                    'bordered': boxed,
                                    'tag':'scale'});
            }








            /**
            * Show the minimum value if its not zero
            */
            if (prop['chart.ymin'] != 0 || prop['chart.noxaxis']) {

                RGraph.Text2(this, {'font': font,
                                    'size': text_size,
                                       'x': xpos,
                                       'y': this.gutterTop,
                                    'text': (this.scale2.min != 0 ? '-' : '') + RGraph.number_format(this,(this.scale2.min.toFixed((prop['chart.scale.decimals']))), units_pre, units_post),
                                  'valign': 'center',
                                  'halign': align,
                                'bordered': boxed,
                                    'tag': 'scale'});
            }

        }
        
        co.fill();
    }



    /**
    * Draws the X axis in the middle
    */
    RGraph.Bar.prototype.Drawlabels_center = function ()
    {
        var ca   = this.canvas;
        var co   = this.context;
        var prop = this.properties;

        var font       = prop['chart.text.font'];
        var numYLabels = prop['chart.ylabels.count'];

        co.fillStyle = prop['chart.text.color'];

        if (prop['chart.xaxispos'] == 'center') {

            /**
            * Draw the top labels
            */
            var text_size  = prop['chart.text.size'];
            var units_pre  = prop['chart.units.pre'];
            var units_post = prop['chart.units.post'];
            var context = co;
            var align   = '';
            var xpos    = 0;
            var boxed   = false;
            var ymin    = prop['chart.ymin'];

            co.fillStyle   = prop['chart.text.color'];
            co.strokeStyle = 'black';

            if (prop['chart.ylabels.inside'] == true) {
                var xpos  = prop['chart.yaxispos'] == 'left' ? this.gutterLeft + 5 : ca.width - this.gutterRight - 5;
                var align = prop['chart.yaxispos'] == 'left' ? 'left' : 'right';
                var boxed = true;
            } else {
                var xpos  = prop['chart.yaxispos'] == 'left' ? this.gutterLeft - 5 : ca.width - this.gutterRight + 5;
                var align = prop['chart.yaxispos'] == 'left' ? 'right' : 'left';
                var boxed = false;
            }












            /**
            * Draw specific Y labels here so that the local variables can be reused
            */
            if (typeof(prop['chart.ylabels.specific']) == 'object' && prop['chart.ylabels.specific']) {

                var labels    = prop['chart.ylabels.specific'];
                var grapharea = ca.height - this.gutterTop - this.gutterBottom;

                // Draw the top halves labels
                for (var i=0; i<labels.length; ++i) {

                    var y = this.gutterTop + ((grapharea / 2) / (labels.length - 1)) * i;

                    RGraph.Text2(this, {'font':font,
                                        'size':text_size,
                                        'x':xpos,
                                        'y':y,
                                        'text':String(labels[i]),
                                        'valign':'center',
                                        'halign':align,
                                        'bordered':boxed,
                                        'tag': 'scale'
                                       });
                }

                // Draw the bottom halves labels
                for (var i=labels.length-1; i>=1; --i) {
                    
                    var y = this.gutterTop  + (grapharea * (i / ((labels.length - 1) * 2) )) + (grapharea / 2);

                    RGraph.Text2(this, {'font':font,
                                        'size':text_size,
                                        'x':xpos,
                                        'y':y,
                                        'text':String(labels[labels.length - i - 1]),
                                        'valign':'center',
                                        'halign':align,
                                        'bordered':boxed,
                                        'tag': 'scale'
                                       });
                }

                return;
            }










            /**
            * Draw the top halfs labels
            */
            for (var i=0; i<this.scale2.labels.length; ++i) {
                var y    = this.gutterTop + this.halfgrapharea - ((this.halfgrapharea / numYLabels) * (i + 1));
                var text = this.scale2.labels[i];
                RGraph.Text2(this, {'font':font, 'size':text_size, 'x':xpos, 'y':y, 'text': text, 'valign':'center', 'halign': align, 'bordered': boxed, 'tag':'scale'});
            }
            
            /**
            * Draw the bottom halfs labels
            */
            for (var i=(this.scale2.labels.length - 1); i>=0; --i) {
                var y = this.gutterTop + ((this.halfgrapharea / numYLabels) * (i + 1)) + this.halfgrapharea;
                var text = this.scale2.labels[i];
                RGraph.Text2(this, {'font':font, 'size':text_size,'x':xpos,'y':y,'text': '-' + text,'valign':'center','halign': align,'bordered': boxed,'tag':'scale'});
            }





            /**
            * Show the minimum value if its not zero
            */
            if (this.scale2.min != 0) {
                RGraph.Text2(this, {'font':font,'size':text_size, 'x':xpos, 'y':this.gutterTop + this.halfgrapharea,'text': RGraph.number_format(this,(this.scale2.min.toFixed((this.properties['chart.scale.decimals']))), units_pre, units_post),'valign':'center', 'valign':'center','halign': align, 'bordered': boxed, 'tag':'scale'});
            }
        }
    }




    /**
    * Draws the X axdis at the bottom (the default)
    */
    RGraph.Bar.prototype.Drawlabels_bottom = function ()
    {
        var co   = this.context;
        var ca   = this.canvas;
        var prop = this.properties;

        var text_size  = prop['chart.text.size'];
        var units_pre  = prop['chart.units.pre'];
        var units_post = prop['chart.units.post'];
        var context    = this.context;
        var align      = prop['chart.yaxispos'] == 'left' ? 'right' : 'left';
        var font       = prop['chart.text.font'];
        var numYLabels = prop['chart.ylabels.count'];
        var ymin       = prop['chart.ymin'];

        co.beginPath();
        co.fillStyle = this.properties['chart.text.color'];
        co.strokeStyle = 'black';

        if (prop['chart.ylabels.inside'] == true) {
            var xpos  = prop['chart.yaxispos'] == 'left' ? this.gutterLeft + 5 : ca.width - this.gutterRight - 5;
            var align = prop['chart.yaxispos'] == 'left' ? 'left' : 'right';
            var boxed = true;
        } else {
            var xpos  = prop['chart.yaxispos'] == 'left' ? this.gutterLeft - 5 : ca.width - this.gutterRight + 5;
            var boxed = false;
        }

        /**
        * Draw specific Y labels here so that the local variables can be reused
        */
        if (prop['chart.ylabels.specific'] && typeof(prop['chart.ylabels.specific']) == 'object') {

            var labels = prop['chart.ylabels.specific'];
            var grapharea = ca.height - this.gutterTop - this.gutterBottom;

            for (var i=0; i<labels.length; ++i) {
                var y = this.gutterTop + (grapharea * (i / (labels.length - 1)));

                RGraph.Text2(this, {'font':font,
                                    'size':text_size,
                                    'x':xpos,
                                    'y':y,
                                    'text': labels[i],
                                    'valign':'center',
                                    'halign': align,
                                    'bordered': boxed,
                                    'tag':'scale'
                                   });
            }

            return;
        }

        var gutterTop      = this.gutterTop;
        var halfTextHeight = this.halfTextHeight;
        var scale          = this.scale;


        for (var i=0; i<numYLabels; ++i) {
            var text = this.scale2.labels[i];
            RGraph.Text2(this, {'font':font,
                                'size':text_size,
                                'x':xpos,
                                'y':this.gutterTop + this.grapharea - ((this.grapharea / numYLabels) * (i+1)),
                                'text': text,
                                'valign':'center',
                                'halign': align,
                                'bordered': boxed,
                                'tag':'scale'});
        }

        
        /**
        * Show the minimum value if its not zero
        */
        if (this.properties['chart.ymin'] != 0 || this.properties['chart.noxaxis']) {
            RGraph.Text2(this, {'font':font,
                                'size':text_size,
                                'x':xpos,
                                'y':this.canvas.height - this.gutterBottom,
                                'text': RGraph.number_format(this,(this.scale2.min.toFixed((this.properties['chart.scale.decimals']))), units_pre, units_post),
                                'valign':'center',
                                'halign': align,
                                'bordered': boxed,
                                'tag':'scale'});
        }
        
        co.fill();
    }


    /**
    * This function is used by MSIE only to manually draw the shadow
    * 
    * @param array coords The coords for the bar
    */
    RGraph.Bar.prototype.DrawIEShadow = function (coords)
    {
        var prevFillStyle = this.context.fillStyle;
        var offsetx       = this.properties['chart.shadow.offsetx'];
        var offsety       = this.properties['chart.shadow.offsety'];
        
        this.context.lineWidth = this.properties['chart.linewidth'];
        this.context.fillStyle = this.properties['chart.shadow.color'];
        this.context.beginPath();
        
        // Draw shadow here
        this.context.fillRect(coords[0] + offsetx, coords[1] + offsety, coords[2], coords[3]);

        this.context.fill();
        
        // Change the fillstyle back to what it was
        this.context.fillStyle = prevFillStyle;
    }


    /**
    * Not used by the class during creating the graph, but is used by event handlers
    * to get the coordinates (if any) of the selected bar
    * 
    * @param object e The event object
    * @param object   OPTIONAL You can pass in the bar object instead of the
    *                          function using "this"
    */
    RGraph.Bar.prototype.getShape = 
    RGraph.Bar.prototype.getBar = function (e)
    {
        // This facilitates you being able to pass in the bar object as a parameter instead of
        // the function getting it from itself
        var obj = arguments[1] ? arguments[1] : this;

        var mouseXY = RGraph.getMouseXY(e);
        var mouseX  = mouseXY[0];
        var mouseY  = mouseXY[1];  
        var canvas  = obj.canvas;
        var context = obj.context;
        var coords  = obj.coords

        for (var i=0; i<coords.length; i++) {

            var left   = coords[i][0];
            var top    = coords[i][1];
            var width  = coords[i][2];
            var height = coords[i][3];

            if (mouseX >= left && mouseX <= (left + width) && mouseY >= top && mouseY <= (top + height)) {

                if (obj.properties['chart.tooltips']) {
                    var tooltip = RGraph.parseTooltipText ? RGraph.parseTooltipText(obj.properties['chart.tooltips'], i) : obj.properties['chart.tooltips'][i];
                }

                // Work out the dataset
                var dataset = 0;
                var idx = i;
                
                while (idx >=  (typeof(obj.data[dataset]) == 'object' ? obj.data[dataset].length : 1)) {
                    if (typeof(obj.data[dataset]) == 'number') {
                        idx -= 1;
                    } else {
                        idx -= obj.data[dataset].length;
                    }
                    
                    dataset++;
                }
                
                if (typeof(obj.data[dataset]) == 'number') {
                    idx = null;
                }


                return {
                        0: obj, 1: left, 2: top, 3: width, 4: height, 5: i,
                        'object': obj, 'x': left, 'y': top, 'width': width, 'height': height, 'index': i, 'tooltip': tooltip, 'index_adjusted': idx, 'dataset': dataset
                       };
            }
        }
        
        return null;
    }


    /**
    * This retrives the bar based on the X coordinate only.
    * 
    * @param object e The event object
    * @param object   OPTIONAL You can pass in the bar object instead of the
    *                          function using "this"
    */
    RGraph.Bar.prototype.getShapeByX = function (e)
    {
        var canvas      = e.target;
        var mouseCoords = RGraph.getMouseXY(e);


        // This facilitates you being able to pass in the bar object as a parameter instead of
        // the function getting it from itself
        var obj = arguments[1] ? arguments[1] : this;


        /**
        * Loop through the bars determining if the mouse is over a bar
        */
        for (var i=0; i<obj.coords.length; i++) {

            var mouseX = mouseCoords[0];
            var mouseY = mouseCoords[1];    
            var left   = obj.coords[i][0];
            var top    = obj.coords[i][1];
            var width  = obj.coords[i][2];
            var height = obj.coords[i][3];

            if (mouseX >= left && mouseX <= (left + width)) {
            
                if (this.properties['chart.tooltips']) {
                    var tooltip = RGraph.parseTooltipText ? RGraph.parseTooltipText(this.properties['chart.tooltips'], i) : this.properties['chart.tooltips'][i];
                }

                

                return {
                        0: obj, 1: left, 2: top, 3: width, 4: height, 5: i,
                        'object': obj, 'x': left, 'y': top, 'width': width, 'height': height, 'index': i, 'tooltip': tooltip
                       };
            }
        }
        
        return null;
    }


    /**
    * When you click on the chart, this method can return the Y value at that point. It works for any point on the
    * chart (that is inside the gutters) - not just points within the Bars.
    * 
    * EITHER:
    * 
    * @param object arg The event object
    * 
    * OR:
    * 
    * @param object arg A two element array containing the X and Y coordinates
    */
    RGraph.Bar.prototype.getValue = function (arg)
    {
        if (arg.length == 2) {
            var mouseX = arg[0];
            var mouseY = arg[1];
        } else {
            var mouseCoords = RGraph.getMouseXY(arg);
            var mouseX      = mouseCoords[0];
            var mouseY      = mouseCoords[1];
        }

        if (   mouseY < this.properties['chart.gutter.top']
            || mouseY > (this.canvas.height - this.properties['chart.gutter.bottom'])
            || mouseX < this.properties['chart.gutter.left']
            || mouseX > (this.canvas.width - this.properties['chart.gutter.right'])
           ) {
            return null;
        }
        
        if (this.properties['chart.xaxispos'] == 'center') {
            var value = (((this.grapharea / 2) - (mouseY - this.properties['chart.gutter.top'])) / this.grapharea) * (this.scale2.max - this.scale2.min)
            value *= 2;
            
            if (value >= 0) {
                value += this.scale2.min;
            } else {
                value -= this.scale2.min;
            }

        } else if (this.properties['chart.xaxispos'] == 'top') {
            var value = ((this.grapharea - (mouseY - this.properties['chart.gutter.top'])) / this.grapharea) * (this.scale2.max - this.scale2.min)
            value = this.scale2.max - value;
            value = Math.abs(value) * -1;
        } else {
            var value = ((this.grapharea - (mouseY - this.properties['chart.gutter.top'])) / this.grapharea) * (this.scale2.max - this.scale2.min)
            value += this.scale2.min;
        }

        return value;
    }


    /**
    * This function can be used when the canvas is clicked on (or similar - depending on the event)
    * to retrieve the relevant Y coordinate for a particular value.
    * 
    * @param int value The value to get the Y coordinate for
    */
    RGraph.Bar.prototype.getYCoord = function (value)
    {
        if (value > this.scale2.max) {
            return null;
        }

        var y;
        var xaxispos = this.properties['chart.xaxispos'];

        if (xaxispos == 'top') {
        
            // Account for negative numbers
            if (value < 0) {
                value = Math.abs(value);
            }

            y = ((value - this.scale2.min) / (this.scale2.max - this.scale2.min)) * this.grapharea;
            y = y + this.gutterTop

        } else if (xaxispos == 'center') {

            y = ((value - this.scale2.min) / (this.scale2.max - this.scale2.min)) * (this.grapharea / 2);
            y = (this.grapharea / 2) - y;
            y += this.gutterTop;

        } else {

            if (value < this.scale2.min) {
                value = this.scale2.min;
            }

            y = ((value - this.scale2.min) / (this.scale2.max - this.scale2.min)) * this.grapharea;

            y = this.canvas.height - this.gutterBottom - y;
        }
        
        return y;
    }



    /**
    * Each object type has its own Highlight() function which highlights the appropriate shape
    * 
    * @param object shape The shape to highlight
    */
    RGraph.Bar.prototype.Highlight = function (shape)
    {
        // Add the new highlight
        RGraph.Highlight.Rect(this, shape);
    }



    /**
    * The getObjectByXY() worker method
    */
    RGraph.Bar.prototype.getObjectByXY = function (e)
    {
        var mouseXY = RGraph.getMouseXY(e);

        if (
               mouseXY[0] >= this.properties['chart.gutter.left']
            && mouseXY[0] <= (this.canvas.width - this.properties['chart.gutter.right'])
            && mouseXY[1] >= this.properties['chart.gutter.top']
            && mouseXY[1] <= (this.canvas.height - this.properties['chart.gutter.bottom'])
            ) {

            return this;
        }
    }



    /**
    * This method handles the adjusting calculation for when the mouse is moved
    * 
    * @param object e The event object
    */
    RGraph.Bar.prototype.Adjusting_mousemove = function (e)
    {
        /**
        * Handle adjusting for the Bar
        */
        if (RGraph.Registry.Get('chart.adjusting') && RGraph.Registry.Get('chart.adjusting').uid == this.uid) {

            // Rounding the value to the given number of decimals make the chart step
            var value   = Number(this.getValue(e));//.toFixed(this.Get('chart.scale.decimals'));
            var shape   = this.getShapeByX(e);

            if (shape) {

                RGraph.Registry.Set('chart.adjusting.shape', shape);

                if (this.stackedOrGrouped && this.properties['chart.grouping'] == 'grouped') {
                    var indexes = RGraph.sequentialIndexToGrouped(shape['index'], this.data);
                    this.data[indexes[0]][indexes[1]] = Number(value);
                } else {
                    this.data[shape['index']] = Number(value);
                }

                RGraph.RedrawCanvas(e.target);
                
                RGraph.FireCustomEvent(this, 'onadjust');
            }
        }
    }


    /*********************************************************************************************************
    * This is the combined bar and Line class which makes creating bar/line combo charts a little bit easier *
    /*********************************************************************************************************/



    RGraph.CombinedChart = function ()
    {
        /**
        * Create a default empty array for the objects
        */
        this.objects = [];
        
        var objects = arguments;

        if (RGraph.is_array(arguments[0])) {
            objects = arguments[0];
        }

        for (var i=0; i<objects.length; ++i) {

            this.objects[i] = objects[i];

            /**
            * Set the Line chart gutters to match the Bar chart gutters
            */
            this.objects[i].Set('chart.gutter.left',  this.objects[0].Get('chart.gutter.left'));
            this.objects[i].Set('chart.gutter.right',  this.objects[0].Get('chart.gutter.right'));
            this.objects[i].Set('chart.gutter.top',    this.objects[0].Get('chart.gutter.top'));
            this.objects[i].Set('chart.gutter.bottom', this.objects[0].Get('chart.gutter.bottom'));

            if (this.objects[i].type == 'line') {
        
                /**
                * Set the line chart hmargin
                */
                this.objects[i].Set('chart.hmargin', ((this.objects[0].canvas.width - this.objects[0].Get('chart.gutter.right') - this.objects[0].Get('chart.gutter.left')) / this.objects[0].data.length) / 2 );
                
                
                /**
                * No labels, axes or grid on the Line chart
                */
                this.objects[i].Set('chart.noaxes', true);
                this.objects[i].Set('chart.background.grid', false);
                this.objects[i].Set('chart.ylabels', false);
            }

            /**
            * Resizing
            */
            if (this.objects[i].Get('chart.resizable')) {
                var resizable_object = this.objects[i];
            }
        }

        /**
        * Resizing
        */
        if (resizable_object) {
            /**
            * This recalculates the Line chart hmargin when the chart is resized
            */
            function myOnresizebeforedraw (obj)
            {
                var gutterLeft = obj.Get('chart.gutter.left');
                var gutterRight = obj.Get('chart.gutter.right');
            
                obj.Set('chart.hmargin', (obj.canvas.width - gutterLeft - gutterRight) / (obj.original_data[0].length * 2));
            }

            RGraph.AddCustomEventListener(resizable_object,
                                          'onresizebeforedraw',
                                          myOnresizebeforedraw);
        }
    }


    /**
    * The Add method can be used to add methods to the CombinedChart object.
    */
    RGraph.CombinedChart.prototype.Add = function (obj)
    {
        this.objects.push(obj);
    }

    
    /**
    * The Draw method goes through all of the objects drawing them (sequentially)
    */
    RGraph.CombinedChart.prototype.Draw = function ()
    {
        for (var i=0; i<this.objects.length; ++i) {
            if (typeof(arguments[i]) == 'function') {
                arguments[i](this.objects[i]);
            } else {
                this.objects[i].Draw();
            }
        }
    }



    /**
    * This function positions a tooltip when it is displayed
    * 
    * @param obj object    The chart object
    * @param int x         The X coordinate specified for the tooltip
    * @param int y         The Y coordinate specified for the tooltip
    * @param objec tooltip The tooltips DIV element
    */
    RGraph.Bar.prototype.positionTooltip = function (obj, x, y, tooltip, idx)
    {
        var coordX     = obj.coords[tooltip.__index__][0];
        var coordY     = obj.coords[tooltip.__index__][1];
        var coordW     = obj.coords[tooltip.__index__][2];
        var coordH     = obj.coords[tooltip.__index__][3];
        var canvasXY   = RGraph.getCanvasXY(obj.canvas);
        var gutterLeft = obj.Get('chart.gutter.left');
        var gutterTop  = obj.Get('chart.gutter.top');
        var width      = tooltip.offsetWidth;
        var height     = tooltip.offsetHeight;
        var value      = obj.data_arr[tooltip.__index__];


        // Set the top position
        tooltip.style.left = 0;
        tooltip.style.top  = canvasXY[1] + coordY - height - 7 + 'px';
        
        /**
        * If the tooltip is for a negative value - position it underneath the bar
        */
        if (value < 0) {
            tooltip.style.top =  canvasXY[1] + coordY + coordH + 7 + 'px';
        }
        
        
        // By default any overflow is hidden
        tooltip.style.overflow = '';
        
        // Inverted arrow
        // data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAFCAMAAACkeOZkAAAAK3RFWHRDcmVhdGlvbiBUaW1lAFNhdCA2IE9jdCAyMDEyIDEyOjQ5OjMyIC0wMDAw2S1RlgAAAAd0SU1FB9wKBgszM4Ed2k4AAAAJcEhZcwAACxIAAAsSAdLdfvwAAAAEZ0FNQQAAsY8L/GEFAAAACVBMVEX/AAC9vb3//+92Pom0AAAAAXRSTlMAQObYZgAAAB1JREFUeNpjYAABRgY4YGRiRDCZYBwQE8qBMEEcAANCACqByy1sAAAAAElFTkSuQmCC

        // The arrow
        var img = new Image();
            img.style.position = 'absolute';
            img.id = '__rgraph_tooltip_pointer__';
            if (value >= 0) {
                img.src = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABEAAAAFCAYAAACjKgd3AAAARUlEQVQYV2NkQAN79+797+RkhC4M5+/bd47B2dmZEVkBCgcmgcsgbAaA9GA1BCSBbhAuA/AagmwQPgMIGgIzCD0M0AMMAEFVIAa6UQgcAAAAAElFTkSuQmCC';
                img.style.top = (tooltip.offsetHeight - 2) + 'px';
            } else {
                img.src = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAFCAMAAACkeOZkAAAAK3RFWHRDcmVhdGlvbiBUaW1lAFNhdCA2IE9jdCAyMDEyIDEyOjQ5OjMyIC0wMDAw2S1RlgAAAAd0SU1FB9wKBgszM4Ed2k4AAAAJcEhZcwAACxIAAAsSAdLdfvwAAAAEZ0FNQQAAsY8L/GEFAAAACVBMVEX/AAC9vb3//+92Pom0AAAAAXRSTlMAQObYZgAAAB1JREFUeNpjYAABRgY4YGRiRDCZYBwQE8qBMEEcAANCACqByy1sAAAAAElFTkSuQmCC';
                img.style.top = '-5px';
            }
            
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
    * This allows for easy specification of gradients
    */
    RGraph.Bar.prototype.parseColors = function ()
    {
        // Set this as a local variable
        var props = this.properties;

        // chart.colors
        var colors = props['chart.colors'];
        if (colors) {
            for (var i=0; i<colors.length; ++i) {
                colors[i] = this.parseSingleColorForGradient(colors[i]);
            }
        }

        // chart.key.colors
        var colors = props['chart.key.colors'];
        if (colors) {
            for (var i=0; i<colors.length; ++i) {
                colors[i] = this.parseSingleColorForGradient(colors[i]);
            }
        }

         props['chart.crosshairs.color']      = this.parseSingleColorForGradient(props['chart.crosshairs.color']);
         props['chart.highlight.stroke']      = this.parseSingleColorForGradient(props['chart.highlight.stroke']);
         props['chart.highlight.fill']        = this.parseSingleColorForGradient(props['chart.highlight.fill']);
         props['chart.text.color']            = this.parseSingleColorForGradient(props['chart.text.color']);
         props['chart.background.barcolor1']  = this.parseSingleColorForGradient(props['chart.background.barcolor1']);
         props['chart.background.barcolor2']  = this.parseSingleColorForGradient(props['chart.background.barcolor2']);
         props['chart.background.grid.color'] = this.parseSingleColorForGradient(props['chart.background.grid.color']);
         props['chart.strokecolor']           = this.parseSingleColorForGradient(props['chart.strokecolor']);
         props['chart.axis.color']            = this.parseSingleColorForGradient(props['chart.axis.color']);
    }



    /**
    * This parses a single color value
    */
    RGraph.Bar.prototype.parseSingleColorForGradient = function (color)
    {
        if (!color || typeof(color) != 'string') {
            return color;
        }

        if (color.match(/^gradient\((.*)\)$/i)) {
            
            var parts = RegExp.$1.split(':');

            // Create the gradient
            var grad = this.context.createLinearGradient(0,this.canvas.height - this.properties['chart.gutter.bottom'], 0, this.properties['chart.gutter.top']);

            var diff = 1 / (parts.length - 1);

            grad.addColorStop(0, RGraph.trim(parts[0]));

            for (var j=1; j<parts.length; ++j) {
                grad.addColorStop(j * diff, RGraph.trim(parts[j]));
            }
        }
            
        return grad ? grad : color;
    }



    RGraph.Bar.prototype.DrawBevel = function ()
    {
       var coords  = this.coords;
       var coords2 = this.coords2;
       var context = this.context;

        if (this.properties['chart.grouping'] == 'stacked') {
            for (var i=0; i<coords2.length; ++i) {
                if (coords2[i] && coords2[i][0] && coords2[i][0][0]) {
                    
                    var x = coords2[i][0][0];
                    var y = coords2[i][0][1];
                    var w = coords2[i][0][2];

                    var arr = [];
                    for (var j=0; j<coords2[i].length; ++j) {
                        arr.push(coords2[i][j][3]);
                    }
                    var h = RGraph.array_sum(arr);

    
                    context.save();
                    
                        context.strokeStyle = 'black';
                    
                        // Clip to the rect
                        context.beginPath();
                        context.rect(x, y, w, h);
                        context.clip();
            
                        // Add the shadow
                        context.shadowColor = 'black';
                        context.shadowOffsetX = 0;
                        context.shadowOffsetY = 0;
                        context.shadowBlur = 20;
            
                        context.beginPath();
                        context.rect(x - 3, y - 3, w + 6, h + 100);
                        context.lineWidth = 5;
                        context.stroke();
                    context.restore();
                }
            }
        } else {

            for (var i=0; i<coords.length; ++i) {
                if (coords[i]) {

                    var x = coords[i][0];
                    var y = coords[i][1];
                    var w = coords[i][2];
                    var h = coords[i][3];
                    
                    var xaxispos = this.properties['chart.xaxispos'];
                    var xaxis_ycoord = ((this.canvas.height - this.gutterTop - this.gutterBottom) / 2) + this.gutterTop;
                    
                    
                    context.save();
                    
                        context.strokeStyle = 'black';
                    
                        // Clip to the rect
                        context.beginPath();
                        context.rect(x, y, w, h);
                        
                        context.clip();
            
                        // Add the shadow
                        context.shadowColor = 'black';
                        context.shadowOffsetX = 0;
                        context.shadowOffsetY = 0;
                        context.shadowBlur =  20;

                        if (xaxispos == 'top' || (xaxispos == 'center' && (y + h) > xaxis_ycoord)) {
                            y = y - 100;
                            h = h + 100;
                        } else {
                            y = y;
                            h = h + 100;
                        }

                        context.beginPath();
                            context.rect(x - 3, y - 3, w + 6, h + 6);
                            context.lineWidth = 5;
                        context.stroke();
                    context.restore();
                }
            }
        }
    }