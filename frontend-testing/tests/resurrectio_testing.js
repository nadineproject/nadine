// This testing is based on using Resurrectio Chrome plugin to record user interaction and then test it again.


var x = require('casper').selectXPath;
casper.options.viewportSize = {width: 320, height: 568};
casper.on('page.error', function(msg, trace) {
   this.echo('Error: ' + msg, 'ERROR');
   for(var i=0; i<trace.length; i++) {
       var step = trace[i];
       this.echo('   ' + step.file + ' (line ' + step.line + ')', 'ERROR');
   }
   this.capture('error.png');
});
casper.test.begin('Resurrectio test', function(test) {
   casper.start('http://127.0.0.1:8000/login/');
   casper.waitForSelector("form#login_form input[name='username']",
       function success() {
           test.assertExists("form#login_form input[name='username']");
           this.click("form#login_form input[name='username']");
       },
       function fail() {
           test.assertExists("form#login_form input[name='username']");
   });
   casper.waitForSelector("input[name='username']",
       function success() {
           this.sendKeys("input[name='username']", "alexandra");
       },
       function fail() {
           test.assertExists("input[name='username']");
   });
   casper.waitForSelector("input[name='password']",
       function success() {
           this.sendKeys("input[name='password']", "password");
       },
       function fail() {
           test.assertExists("input[name='password']");
   });
   casper.waitForSelector("form#login_form button[type=submit][value='Login']",
       function success() {
           test.assertExists("form#login_form button[type=submit][value='Login']");
           this.click("form#login_form button[type=submit][value='Login']");
       },
       function fail() {
           test.assertExists("form#login_form button[type=submit][value='Login']");
   });
   /* submit form */
   casper.waitForSelector(x("//a[normalize-space(text())='Member List']"),
       function success() {
           test.assertExists(x("//a[normalize-space(text())='Member List']"));
           this.click(x("//a[normalize-space(text())='Member List']"));
       },
       function fail() {
           test.assertExists(x("//a[normalize-space(text())='Member List']"));
   });
   casper.waitForSelector(x("//a[normalize-space(text())='View Members']"),
       function success() {
           test.assertExists(x("//a[normalize-space(text())='View Members']"));
           this.click(x("//a[normalize-space(text())='View Members']"));
       },
       function fail() {
           test.assertExists(x("//a[normalize-space(text())='View Members']"));
   });
   casper.waitForSelector("form#site-search-form input[name='terms']",
       function success() {
           test.assertExists("form#site-search-form input[name='terms']");
           this.click("form#site-search-form input[name='terms']");
       },
       function fail() {
           test.assertExists("form#site-search-form input[name='terms']");
   });
   casper.waitForSelector("input[name='terms']",
       function success() {
           this.sendKeys("input[name='terms']", "jacob\r");
       },
       function fail() {
           test.assertExists("input[name='terms']");
   });
   casper.waitForSelector("form#site-search-form input[type=submit][value='Search']",
       function success() {
           test.assertExists("form#site-search-form input[type=submit][value='Search']");
           this.click("form#site-search-form input[type=submit][value='Search']");
       },
       function fail() {
           test.assertExists("form#site-search-form input[type=submit][value='Search']");
   });
   /* submit form */
   casper.waitForSelector(x("//a[normalize-space(text())='Jacob Sayles']"),
       function success() {
           test.assertExists(x("//a[normalize-space(text())='Jacob Sayles']"));
           this.click(x("//a[normalize-space(text())='Jacob Sayles']"));
       },
       function fail() {
           test.assertExists(x("//a[normalize-space(text())='Jacob Sayles']"));
   });

   casper.run(function() {test.done();});
});
