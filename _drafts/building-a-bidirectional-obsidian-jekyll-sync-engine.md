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

```chart
scripts/sync_engine/
├── core/
│   ├── engine.py    # The brains of the operation
│   ├── types.py     # The vocabulary
│   ├── conflict.py  # The peacekeeper
│   └── atomic.py    # The safety net
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

### Atomic Operations 🛡️

Because nobody likes corrupted files or half-synced posts, we use atomic operations with automatic rollback:

1. **Safe File Writes**

   ```python
   # Write files safely with automatic backup
   with atomic.atomic_write(post_path) as f:
       f.write(content)  # If anything fails, original is restored
   ```

2. **Operation Tracking**

   ```python
   # Every operation is tracked
   operation = AtomicOperation(
       operation_type='write',
       source_path=src,
       target_path=dst,
       backup_path=backup
   )
   ```

3. **Automatic Rollback**
   - Creates backups before operations
   - Restores from backup if anything fails
   - Cleans up old backups automatically
   - Tracks operation history for debugging

### Media Magic 🪄

The media handler is where things get really fancy. It's like having a personal assistant for your images and attachments:

1. **Smart Path Resolution**

   ```python
   # Your Obsidian link (now with absolute paths!)
   ![[atomics/2024/12/03/my cool image.png]]
   
   # Gets magically transformed to
   ![my cool image](/assets/img/posts/atomics-2024-12-03-my-cool-image-a1b2c3d4.png)
   ```

2. **Image Optimization**
   - Automatically resizes large images (max 1200px width)
   - Optimizes JPEGs and PNGs for web
   - Converts RGBA to RGB with white background
   - Supports WebP for modern browsers
   - Preserves directory structure in filenames
   - Handles absolute vault paths for reliable linking

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
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure your paths in `.env`:

   ```bash
   # Copy example config
   cp .env.example .env
   
   # Edit with your paths
   VAULT_ROOT=/path/to/your/vault
   VAULT_MEDIA_PATH=atomics
   VAULT_POSTS_PATH=_posts
   
   JEKYLL_ROOT=/path/to/your/jekyll
   JEKYLL_ASSETS_PATH=assets/img/posts
   JEKYLL_POSTS_PATH=_posts
   ```

4. Let it rip:

   ```python
   from sync_engine import SyncEngineV2
   from dotenv import load_dotenv
   import os
   
   # Load config from .env
   load_dotenv()
   
   config = {
       'vault_root': os.getenv('VAULT_ROOT'),
       'vault_media': os.getenv('VAULT_MEDIA_PATH'),
       'jekyll_root': os.getenv('JEKYLL_ROOT'),
       'jekyll_assets': os.getenv('JEKYLL_ASSETS_PATH')
   }
   
   engine = SyncEngineV2(config)
   engine.sync()
   ```

## The Magic Sauce

The real magic happens in the status handling. Want to publish a post? Just add this to your Obsidian note's frontmatter:

```yaml
---
title: My Awesome Post
status: published  # The magic word!
image: ![[atomics/2024/12/03/my-featured-image.jpg]]  # Will be processed automatically
---

Here's a cool image: ![[atomics/2024/12/03/another-image.png]]
```

And voilà! Your post is ready for its internet debut, complete with optimized images. Want to keep it as a draft? Use `status: draft`. Want to keep it private? `status: private` or just leave it out entirely.

## Testing & Verification

The engine comes with a comprehensive test suite to ensure everything works smoothly:

```bash
# Run all tests
python -m pytest

# Run specific test modules
python -m pytest scripts/sync_engine/tests/test_media_sync.py
```

The tests cover:

1. **Media Handling**
   - Absolute path resolution
   - Frontmatter image handling
   - Path sanitization
   - Bidirectional sync
   - Image optimization

2. **Core Engine**
   - File change detection
   - Conflict resolution
   - Atomic operations
   - Config handling

3. **End-to-End**
   - Full sync cycles
   - Migration process
   - Error recovery
   - Performance benchmarks

Each component is tested both with mock data for isolation and with real vault data for integration verification.

### Change Detection: The File Detective 🔍

Remember our friend the meticulous librarian? Well, they just got a promotion to detective! Our change detection system now has a fancy new way of tracking files:

```python
def detect_changes(self) -> List[SyncState]:
    # Get the lay of the land
    obsidian_posts = {p.name: p for p in self.posts_path.glob('*.md')}
    jekyll_posts = {p.name: p for p in self.jekyll_posts.glob('*.md')}
    
    # Find ALL the posts (union of sets, because we're fancy like that)
    all_posts = set(obsidian_posts) | set(jekyll_posts)
    
    # Time to play detective
    for post_name in all_posts:
        if post_name in obsidian_posts and post_name in jekyll_posts:
            # Found in both places - let's see what's changed
            self._check_modifications(obsidian_posts[post_name], jekyll_posts[post_name])
        elif post_name in obsidian_posts:
            # Only in Obsidian - new kid on the block
            self._handle_obsidian_only(obsidian_posts[post_name])
        else:
            # Only in Jekyll - either deleted or Jekyll's being creative
            self._handle_jekyll_only(jekyll_posts[post_name])
```

This new system is like having a security camera that can spot:

- New posts popping up (like mushrooms after rain)
- Deleted posts (gone, but not forgotten)
- Modified posts (sneaky little changes)
- Status changes (from shy draft to proud published post)

## The Test Suite: Because Trust Issues are Healthy

Remember those tests I mentioned? Well, they've grown up and now we have a proper test suite that would make a QA engineer proud:

```bash
# Run the whole shebang
python -m pytest scripts/sync_engine/tests/

# Just test the media stuff (because images are special)
python -m pytest scripts/sync_engine/tests/test_media_*.py

# Check if our file detective is doing their job
python -m pytest scripts/sync_engine/tests/test_file_changes.py
```

Current test coverage is at a whopping 90% (the remaining 10% is probably just comments... right? 😅)

### What We Test

1. **Media Handling (100% covered)**
   - Image processing (because nobody likes blurry cat pictures)
   - Error handling (for when that PNG is actually a text file in disguise)
   - Reference extraction (finding all those `![[]]` needles in the markdown haystack)
   - Path generation (making sure your images don't end up in digital limbo)

2. **Bidirectional Sync (100% covered)**
   - Obsidian → Jekyll (the forward pass)
   - Jekyll → Obsidian (the reverse uno card)
   - Status handling (draft/published/private - the three states of content)

3. **Core Engine (90% covered)**
   - File change detection (our new detective system)
   - Conflict resolution (for when Obsidian and Jekyll can't agree)
   - Error recovery (because stuff happens)

4. **Coming Soon™**
   - Atomic operations (for when you want your sync to be really, really safe)
   - Real-time sync (because who has time to click buttons?)
   - A better UI for conflicts (less "merge conflict", more "choose your adventure")

## Lessons Learned (The Hard Way)

1. **State is King**: Keeping track of sync state is like keeping track of your keys - lose it, and you'll spend hours looking for what changed.

2. **Content Comparison is Tricky**: Turns out, comparing files is like comparing pizzas - just because they look the same doesn't mean they are the same.

3. **Error Handling is Your Friend**: Things will go wrong. It's not a bug, it's a feature opportunity!

4. **Test Everything**: And then test it again. And one more time for good measure.
