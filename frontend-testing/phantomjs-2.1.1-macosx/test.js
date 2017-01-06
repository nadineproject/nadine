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
      if (element == "post") {
        //insert testing username
        form.elements["username"].value="alexandra";
        //insert testing password
        form.elements["password"].value="hellocats";
      }
    });
  },
  function() {
    page.evaluate(function() {
      var form = document.getElementById("login_form");
      var element = form.getAttribute('method');
      if (element == "post") {
        form.submit();
      }
    });
  },
  function() {
    page.render('loggedin.png');
    page.evaluate(function() {
      console.log('Done login.');
    });
  },
  function() {
    page.open(url + '/member/edit/alexandra');
  },
  function() {
    
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
