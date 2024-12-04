---
title: "Building a Bidirectional Obsidian-Jekyll Sync Engine (or: How I Learned to Stop Worrying and Love the Sync)"
tags:
    - python
    - obsidian
    - jekyll
    - automation
    - development
---

You know what they say about syncing? It's all about timing! 🥁

(I'll show myself out... but not before I tell you about this cool sync engine I built!)

## The Problem

Picture this: You're happily writing in Obsidian, your thoughts flowing like a mountain stream, when suddenly you realize you want to share some of these gems with the world. But wait! Your blog runs on Jekyll, and copying files manually is about as fun as explaining to your grandma why her computer needs to sync with the cloud.

"Why not just write directly in Jekyll?" I hear you ask. Well, my friend, that's like asking why I don't just write my shopping list on individual sticky notes scattered around the house. Obsidian is my second brain, my digital garden, my... okay, I'll stop with the metaphors.

## The Solution

Enter the Obsidian-Jekyll Sync Engine v2 (or as I like to call it, "The Thing That Finally Made My Blog Posts Stop Playing Hide and Seek"). It's a Python-based tool that:

1. Watches your Obsidian vault
2. Picks up posts marked for publishing
3. Magically transforms them into Jekyll-compatible posts
4. Handles all the boring stuff like image processing
5. And (drumroll please 🥁) even syncs changes back from Jekyll to Obsidian!

## How It Works

### The Core Engine

At its heart, the sync engine is like a very meticulous librarian (but faster and with less shushing). It keeps track of every file's state using a fancy state machine:

```python
class PostStatus(Enum):
    PUBLISHED = "published"  # Ready for the world to see
    DRAFT = "draft"         # Still cooking
    PRIVATE = "private"     # Shh, it's a secret
    NONE = None            # Just a regular note
```

### The Smart Parts

The engine is split into modular components (because who doesn't love a good modular design?):

```
scripts/sync_engine/
├── core/
│   ├── engine.py    # The brains of the operation
│   ├── types.py     # The vocabulary
│   └── conflict.py  # The peacekeeper
└── handlers/
    ├── post.py      # The post whisperer
    └── media.py     # The image wizard
```

### Bidirectional Sync

Here's where it gets interesting. The engine doesn't just push changes one way - it's like a digital diplomat, negotiating changes between Obsidian and Jekyll:

1. **Obsidian → Jekyll**:
   - Converts your Obsidian wikilinks to proper Jekyll paths
   - Handles frontmatter translation
   - Processes images (because no one likes broken image links)

2. **Jekyll → Obsidian**:
   - Updates content while preserving Obsidian metadata
   - Keeps your links and formatting intact
   - Never messes with your precious Obsidian structure

### Conflict Resolution 🤝

Sometimes both sides change the same file (we've all been there). The engine handles this like a pro mediator:

1. **Smart Detection**
   ```python
   # Detect changes using content hashes
   content_differs = obsidian_hash != jekyll_hash
   frontmatter_differs = obsidian_fm != jekyll_fm
   ```

2. **Resolution Strategy**
   - If only frontmatter differs: Keep Obsidian's version (it's your source of truth)
   - If content differs: Use the most recently modified version
   - If Jekyll is newer: Only update content in Obsidian, preserve metadata
   - If Obsidian is newer: Update everything in Jekyll

3. **Helpful Diffs**
   ```python
   # When conflicts occur, see what changed
   diff = engine.get_content_diff(obsidian_file, jekyll_file)
   print(f"Changes:\n{diff}")
   ```

### Media Magic 🪄

The media handler is where things get really fancy. It's like having a personal assistant for your images and attachments:

1. **Smart Path Resolution**
   ```python
   # Your Obsidian link
   ![[my cool image.png]]
   
   # Gets magically transformed to
   ![my cool image](/assets/img/posts/my-cool-image-a1b2c3d4.png)
   ```

2. **Image Optimization**
   - Automatically resizes large images (max 1200px width)
   - Optimizes JPEGs and PNGs for web
   - Converts RGBA to RGB with white background
   - Supports WebP for modern browsers

3. **Asset Management**
   - Tracks used files to avoid duplicates
   - Cleans up unused assets automatically
   - Maintains a mapping between original and processed files

4. **Bidirectional Media Sync**
   - If you edit an image in Jekyll, it syncs back to Obsidian
   - Preserves original filenames in Obsidian
   - Uses content hashes for reliable tracking

## Setting It Up

Want to try it yourself? Here's how:

1. Clone the repo:

   ```bash
   git clone https://github.com/asbjborg/asbjborg.github.io.git
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure your paths:

   ```python
   config = {
       'vault_path': '~/Documents/Obsidian/MyVault',
       'blog_path': '~/blog'
   }
   ```

4. Let it rip:

   ```python
   from sync_engine import SyncEngineV2
   
   engine = SyncEngineV2(config)
   engine.sync()
   ```

## The Magic Sauce

The real magic happens in the status handling. Want to publish a post? Just add this to your Obsidian note's frontmatter:

```yaml
---
title: My Awesome Post
status: published  # The magic word!
image: ![[my-featured-image.jpg]]  # Will be processed automatically
---

Here's a cool image: ![[another-image.png]]
```

And voilà! Your post is ready for its internet debut, complete with optimized images. Want to keep it as a draft? Use `status: draft`. Want to keep it private? `status: private` or just leave it out entirely.
