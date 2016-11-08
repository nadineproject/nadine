//This test.js currently logs in the user and redirects to user index page

var url = 'http://127.0.0.1:8000';

var page = new WebPage(), testindex = 0, loadInProgress = false, links, brokenLinks = [];

page.onConsoleMessage = function(msg) {
  console.log(msg);
};

page.onLoadStarted = function() {
  loadInProgress = true;
  console.log("load started");
};

page.onLoadFinished = function() {
  loadInProgress = false;
  console.log("load finished");
};

var steps = [
  function() {
    page.open(url + '/login');
  },
  function() {
    page.evaluate(function() {
      var form = document.getElementById("login_form");
      var element = form.getAttribute('method');
      if (element == "POST") {
        //insert testing username
        form.elements["username"].value="";
        //insert testing password
        form.elements["password"].value="";
      }
    });
  },
  function() {
    page.evaluate(function() {
      var form = document.getElementById("login_form");
      var element = form.getAttribute('method');
      if (element == "POST") {
        form.submit();
      }
    });
  },
  function() {
    // page.render('done.png');
    page.evaluate(function() {
      console.log('Done login.');
    });
  },
  function() {
    page.open(url + '/member/profile/alexandra');
  },
  function() {
    links = page.evaluate(function(links) {
       var as = document.getElementsByTagName('a');
       var hrefs = [];
       for (var k = 0; k < as.length; k++ ){
         hrefs.push(as[k].getAttribute('href'));
       }
       return hrefs;
    }, links);
  },
  function() {
    for(var j = 0; j < (links.length - 5); j++) {
      //TODO fix async issue with this to test links.
      page = new WebPage();
      page.open(url + links[3], function() {
        page.render('img/page' + j + '.png');
      })
    }
  },
  function() {
    page.render('done.png');
  }
];


interval = setInterval(function(links) {
  if (!loadInProgress && typeof steps[testindex] == "function") {
    console.log("step " + (testindex + 1));
    steps[testindex]();
    testindex++;
  }
  if (typeof steps[testindex] != "function") {
    console.log("test complete!");
    phantom.exit();
  }
}, 50);
