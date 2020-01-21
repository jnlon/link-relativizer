# link-relativizer

A Python3 program that converts absolute links to relative links in a directory
of HTML files.

This script will search and replace absolute links with a specified domain and
transform them so they become relative to files in a local directory.

## Purpose and Example

This script can be useful when scraping websites for offline archival/viewing.
Consider a website that uses hardcoded absolute links that point to the same
content hosted on 2 different subdomains, eg. www.example.com vs. example.com.
Both sites can be retrieved individually, copied into a shared folder, then
link-relativzer can be used integrate their links so they reference the same
content like so:

```
$ cp -r www.example.com/. example.com/
$ link-relativizer.py -d www.example.com -p example.com/ -w
$ link-relativizer.py -d example.com -p example.com/ -w
```

Now any absolute links referencing "www.example.com" or "example.com" will
be relative to the "example.com/" directory, transforming it into a single
portable webroot.

## Usage

**IMPORTANT:** It is strongly suggested to make a backup of your webroot before
applying the `-w` option, which modifies files in-place.


```
usage: link-relativizer.py [-h] -p webroot -d domain [-w] [-v]

Convert absolute links to relative links in HTML files under a webroot

optional arguments:
  -h, --help  show this help message and exit
  -p webroot  Path to webroot directory containing HTML files
  -d domain   Domain used in absolute links to be made relative
  -w          Write all link substutions to file(s)
  -v          Verbose mode, print all link substutions
```

## Caveats

- This script may not work on windows due to its reliance on the `posixpath` module

- The current link replacement algorithm is naive and in some corner-cases
  may overwrite non-link website content, for example strings that look like
  absolute references wrapped in &lt;pre&gt; tags
