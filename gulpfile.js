'use strict';

const gulp = require('gulp');
const webpack = require('webpack-stream');
const webpackUglifyJs = require('uglifyjs-webpack-plugin')
const sass = require('gulp-sass');
const tildeImporter = require('node-sass-tilde-importer');
const browserSync = require('browser-sync');
const sourcemaps = require('gulp-sourcemaps');
const autoprefixer = require('gulp-autoprefixer');
const uglify = require('gulp-uglify');
const concat = require('gulp-concat');
const rename = require('gulp-rename');
const imagemin = require('gulp-imagemin');
const changed = require('gulp-changed');
const del = require('del');
const sequence = require('run-sequence');
const pkg = require('./package.json')

var production = false;

const file = {
  html:   'src/**/*.html',
  scss:   'assets/scss/**/*.scss',
  js:     'assets/js/src/**/*.js',
}

const page = {
  js:     'assets/js/src/page.js',
  scss:   'assets/scss/page.scss',
}

const dir = {
  css:    'assets/css/',
  js:     'assets/js/',
  font:   'assets/fonts/',
}



/*
|--------------------------------------------------------------------------
| Serve
|--------------------------------------------------------------------------
|
*/
function reload(done) {
  browserSync.reload();
  done();
};

function serve(done) {
  gulp.watch( file.scss, scss );
  gulp.watch( file.js, gulp.series(js, reload));
  gulp.watch( file.html, reload );
  done();
};


/*
|--------------------------------------------------------------------------
| SASS
|--------------------------------------------------------------------------
|
*/
function scss() {

  var stream = gulp.src(page.scss)
    .pipe( sourcemaps.init() )
    .pipe( rename( { suffix: '.min' } ) )
    .pipe( sass({ importer: tildeImporter, outputStyle: 'compressed' }).on('error', sass.logError) )
    .pipe( autoprefixer())
    .pipe( sourcemaps.write('.') )
    .pipe( gulp.dest(dir.css) )
    .pipe( browserSync.stream() );

  // Create unminified version if it's in production mode
  if ( production ) {
    stream = gulp.src(page.scss)
      .pipe( sourcemaps.init() )
      .pipe( sass({importer: tildeImporter}).on('error', sass.logError) )
      .pipe( autoprefixer())
      .pipe( sourcemaps.write('.') )
      .pipe( gulp.dest(dir.css) );
  }

  return stream;

};


/*
|--------------------------------------------------------------------------
| JS
|--------------------------------------------------------------------------
|
*/
function js() {
  return gulp.src(page.js)
    .pipe(webpack({
      mode: 'none',
      devtool: 'source-map',
      output: {
        filename: 'page.min.js'
      }
    }))
    .pipe( gulp.dest(dir.js) );

};


function jsProductionMinified() {
  return gulp.src(page.js)
    .pipe(webpack({
      mode: 'production',
      devtool: 'source-map',
      output: {
        filename: 'page.min.js'
      },
      performance: {
        hints: false
      }
    }))
    .pipe( gulp.dest(dir.js) );
};


function jsProductionExpanded() {
  return gulp.src(page.js)
    .pipe(webpack({
      mode: 'none',
      devtool: 'source-map',
      output: {
        filename: 'page.js'
      }
    }))
    .pipe( gulp.dest(dir.js) );
};


/*
|--------------------------------------------------------------------------
| Copy
|--------------------------------------------------------------------------
|
*/
function copyFonts(done) {
  //gulp.src( 'node_modules/@fortawesome/fontawesome-free-webfonts/webfonts/*').pipe(gulp.dest(dir.font));
  gulp.src( 'node_modules/font-awesome/fonts/*').pipe(gulp.dest(dir.font));
  gulp.src( 'node_modules/themify-icons/themify-icons/fonts/*').pipe(gulp.dest(dir.font));
  gulp.src( 'node_modules/et-line/fonts/*').pipe(gulp.dest(dir.font));
  done();
};

function distCopy(done) {
  gulp.src('assets/css/page.min.*').pipe(gulp.dest('dist/css'));
  gulp.src('assets/js/page.min.*').pipe(gulp.dest('dist/js'));
  done();
};


/*
|--------------------------------------------------------------------------
| Clean /dist directory
|--------------------------------------------------------------------------
|
*/
function distClean() {
  return del('dist/');
};

/*
|--------------------------------------------------------------------------
| Img
|--------------------------------------------------------------------------
|
*/
function img() {
  return gulp.src('assets/img/**/*.{jpg,jpeg,png,gif}')
    .pipe( imagemin() )
    .pipe( gulp.dest('assets/img/') );
};

/*
|--------------------------------------------------------------------------
| Tasks
|--------------------------------------------------------------------------
|
*/
function setProductionMode(done) {
  production = true;
  done();
}

function setDevMode(done) {
  production = false;
  done();
}


exports.dev     = gulp.series(copyFonts, scss, js);
exports.dist    = gulp.series(setProductionMode, distClean, copyFonts, scss, jsProductionMinified, jsProductionExpanded, distCopy, setDevMode);
exports.watch   = serve;
exports.default = serve;
