// To test this file, make sure CapserJs is installed on local machine
// (brew install casperjs) then use code 'casperjs test homelinktesting.js'

// This tests to make sure all urls are valid on the member homepage

var url = 'http://127.0.0.1:8000';
var links;

username = casper.cli.get('username');
password = casper.cli.get('password');

casper.on("page.error", function(msg, trace) {
    this.echo("Page Error: " + msg, "ERROR");
});

casper.test.begin('Home page links all return 200', function suite(test) {
  casper.start(url + '/login', function() {
      test.assertTitle("Login | Office Nomads", "Login page title is the one expected");
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

  casper.then(function() {
    test.assertTitle("Office Nomads", "Homepage title is ok");
    test.assertUrlMatch(/member/, "Homepage url correct");
  });

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
        test.assertEquals(this.currentHTTPStatus, 200);
      });
    });
  });

  casper.run(function() {
      test.done();
  });
});
