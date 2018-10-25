// This tests the mobile navigation in Member Application to make sure that the side-navigation opens up on smaller screens
// To run this test enter 'casperjs test tests/mobil_nav.js --username=USERNAME --password=PASSWORD'

var x = require('casper').selectXPath;
username = casper.cli.get('username');
password = casper.cli.get('password');

casper.options.viewportSize = {width: 320, height: 568};

casper.on('page.error', function(msg, trace) {
   this.echo('Error: ' + msg, 'ERROR');
   for(var i=0; i<trace.length; i++) {
       var step = trace[i];
       this.echo('   ' + step.file + ' (line ' + step.line + ')', 'ERROR');
   }
});

casper.test.begin('Member App on Mobile Test', function(test) {
   casper.start('http://127.0.0.1:8000/member/');
   casper.userAgent("Mozilla/5.0 (compatible; MSIE 10.0; Windows Phone 8.0; Trident/6.0; IEMobile/10.0; ARM; Touch; NOKIA; Lumia 820)");
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
           this.sendKeys("input[name='username']", username);
       },
       function fail() {
           test.assertExists("input[name='username']");
   });
   casper.waitForSelector("input[name='password']",
       function success() {
           this.sendKeys("input[name='password']", password);
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
   casper.waitForSelector('.side-nav',
       function success() {
         test.assertNotVisible('#nav-mobile');
         this.click('.side-nav li:first-child a');
       },
       function fail() {
           test.assertNotVisible('#nav-mobile');
   });

   casper.then(function() {
     test.assertUrlMatch('/member/help', 'Navigation to help link via mobile navigation working.')
   })

   casper.run(function() {test.done();});
});
