# Blogmaker

This is an ultra-simple self-hosted blog publishing solution.

### Dependencies

* pandoc
* rsync

### How to use

See the [posts](./posts) directory for what a post should look like. Posts must be written in [markdown](https://daringfireball.net/projects/markdown/syntax), and filenames must end in `.md`. Dates must be in `yyyy/mm/dd` format. All posts must be in the top-level `posts` directory.

If you need a post to use MathJaX to format LaTeX equations, add the line

```
[pandoc]: <> (--mathjax)
```

to the config at the top of the post.

To build the full site, run `./publish.py`. To compile a single post, run `./publish.py posts/name_of_post.md`. Use `./publish.py --sync` to upload the latest version of your site to your server after the local build looks right.

For the server, the simplest setup is to use any VPS, `apt install apache2`, make sure Apache is running, and point `website_root` at the directory your vhost serves.

### Config

`config.md` now expects:

* `title`: the visible site title
* `description`: a short intro used in the header, feed, and metadata
* `domain`: the canonical public URL used for RSS and canonical links
* `icon`: an absolute URL for your icon
* `profile`: optional SNS profile URL shown in the site nav/footer
* `server`: SSH destination for `rsync`
* `website_root`: target directory on the server
* `homepage_category`: optional category filter for the archive page

### SNS setup

For `elrakabawi.sol`, the most practical browser-facing setup is:

* Publish the repo with GitHub Pages using `.github/workflows/deploy-pages.yml`.
* Use `https://elrakabawi.sol.site` as the custom Pages domain and canonical URL in `config.md`.
* Configure `elrakabawi.sol` in SNS Manager so the `Sol.site` records point `elrakabawi.sol.site` to GitHub Pages.

According to the current SNS docs, `Sol.site` is the standard bridge from your `.sol` name to a regular web URL, while Brave can also resolve `.sol` names directly.

### GitHub Pages flow

1. Push `main` to GitHub.
2. In the repository settings, open **Pages** and set the source to **GitHub Actions**.
3. Let the workflow publish the site.
4. In **Pages**, set the custom domain to `elrakabawi.sol.site`.
5. In SNS Manager for `elrakabawi.sol`, use **Configure Sol.site** and add these `A` records for `elrakabawi.sol.site`:
   `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
6. Optionally add these `AAAA` records for IPv6:
   `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`
7. Wait for DNS and certificate propagation, then verify `https://elrakabawi.sol.site`.

### Misc

The generated site copies files from `css/`, `scripts/`, and `images/` into `site/`.
