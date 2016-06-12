// Dependencies
var gulp = require('gulp');
var nodemon = require('gulp-nodemon');
 
// Task
gulp.task('default', function() {
	// listen for changes
	// configure nodemon
	nodemon({
		// the script to run the app
		// script: 'node .',
		ignore: ['db.json'],
		ext: 'js json'
	}).on('restart', function(){
	})
})
