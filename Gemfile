# frozen_string_literal: true

source "https://rubygems.org"

gem "jekyll-theme-chirpy", "~> 7.2"
gem "jekyll", "~> 4.3.2"
gem "webrick"
gem "base64"     # Required for Ruby 3.3
gem "bigdecimal" # Required for Ruby 3.3
gem "csv"        # Required for Ruby 3.3

group :test do
  gem "html-proofer", "~> 5.0"
end

group :jekyll_plugins do
  gem "jekyll-seo-tag"
  gem "jekyll-paginate"
  gem "jekyll-sitemap"
  gem "jekyll-archives"
  gem "jekyll-redirect-from"
end

platforms :mingw, :x64_mingw, :mswin, :jruby do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end

gem "wdm", "~> 0.1.1", :platforms => [:mingw, :x64_mingw, :mswin]
