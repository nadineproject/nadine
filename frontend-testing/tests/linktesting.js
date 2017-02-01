// To test this file, make sure CapserJs is installed on local machine
// (brew install casperjs) then use code 'casperjs test tests/linktesting.js --username='YOUR_USERNAME' --password='YOUR_PASSWORD' --path='/GIVEN_PATH/' --log-level=debug'

// This tests to make sure all urls are valid on given page
var url = 'http://127.0.0.1:8000';
var links;
username = casper.cli.get('username');
password = casper.cli.get('password');
path = casper.cli.get('path');

casper.options.viewportSize = {width: 1100, height: 616};

casper.on("page.error", function(msg, trace) {
    this.echo("Page Error: " + msg, "ERROR");
    this.capture('img/login-error.png');
});

casper.test.begin('Links from given path return 200', function suite(test) {
  casper.start(url + path, function() {
      // test.assertTitle("Login | Office Nomads", "Login page title is the one expected");
      test.assertExists('form[method="post"]', "login form is found");
      this.fill("form[method='post']", {
        'username': username,
        'password': password
      }, true)
  });

  casper.then(function() {
    this.log('Logging in', 'debug');
    this.evaluate(function() {
      document.getElementById('loginonly-btn').click();
    })
  })

  casper.then(function getLinks() {
    links = this.evaluate(function(){
      var links = document.getElementsByTagName('a');
      links = Array.prototype.map.call(links,function(link){
          return link.getAttribute('href');
      });
      return links;
    });
  });

  casper.then(function() {
    this.each(links,function(self,link) {
      path = url + link;
      self.thenOpen(path,function(a) {
        test.assertEquals(this.currentHTTPStatus, 200, link + ' has status code 200');
      });
    });
  });

  casper.run(function() {
    require('utils').dump(this.result.log);
    test.done();
  });
});
