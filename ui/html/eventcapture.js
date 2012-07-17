
	var events = [];
	function rerouter(e) {
		events.push( e);
		routeEvent(e);
		return true;
	}
	function wcapture() {
   		window.captureEvents( Event.BLUR | Event.CHANGE | Event.FOCUS | Event.CLICK | Event.DBLCLICK );
	   	window.onblur = rerouter;
   		window.onchange = rerouter;
	   	window.onfocus = rerouter;
	}	
	function wrelease() {
   		window.releaseEvents( Event.BLUR | Event.CHANGE | Event.FOCUS | Event.CLICK | Event.DBLCLICK );
	}

	function dump1(e) {
		var r = "events is " + events.length + "\n";
		if (0) {
		        r = events.join( "\n ");
		} else {
			for (var i =0; i< events.length; i+=1) {
				var ee = events[i];
				r += "event type: " + " "+ee+" "+ee.target + ee.target.name;
				r += '\n';
				//r += '; ';				
			}
		}
		events.length = 0;
   		return r;
	}
	function dump(e) {
		var r = dump1(e);
		alert( r);
		return true;
	}
	wcapture();
	window.onmove = dump;
	window.onClick = dump;
	window.onDblClick = dump;
	dump(1);
