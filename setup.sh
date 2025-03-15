#!/bin/bash

# Create base directory structure
mkdir -p site/docs/pages
mkdir -p site/docs/public

# Create pages directory structure for cleaner URLs
mkdir -p site/docs/pages/getting-started
mkdir -p site/docs/pages/core-uploading
mkdir -p site/docs/pages/utility-functions
mkdir -p site/docs/pages/configuration
mkdir -p site/docs/pages/reference

# Create landing page
cat > site/docs/pages/index.mdx << 'EOF'
---
layout: landing
---

import { HomePage } from 'vocs/components'

<HomePage.Root>
  <HomePage.Logo />
  <HomePage.Tagline>Simple AWS S3 Upload Utility</HomePage.Tagline>
  <HomePage.Description>
    A lightweight, powerful tool for uploading, organizing, and managing files in Amazon S3 buckets.
  </HomePage.Description>
  <HomePage.Buttons>
    <HomePage.Button href="/getting-started" variant="accent">Get Started</HomePage.Button>
    <HomePage.Button href="https://github.com/yourusername/s3u">GitHub</HomePage.Button>
  </HomePage.Buttons>
</HomePage.Root>
EOF

# Getting Started page
cat > site/docs/pages/getting-started/index.mdx << 'EOF'
---
layout: docs
---

# Getting Started

Learn how to install and set up S3U for your AWS environment.

## Installation

A section about installing the S3U tool.

## AWS Configuration

A section about configuring AWS credentials and access.

## Setup

A section about initial setup steps after installation.
EOF

# Core Uploading page
cat > site/docs/pages/core-uploading/index.mdx << 'EOF'
---
layout: docs
---

# Core Uploading

Learn about the core uploading features of S3U.

## Interactive Upload Process

A section about the interactive upload interface.

## Media Optimization

A section about automatic media optimization.

## Concurrent Uploads

A section about handling multiple uploads simultaneously.

## Subfolder Handling

A section about organizing uploads into subfolders.
EOF

# Utility Functions page
cat > site/docs/pages/utility-functions/index.mdx << 'EOF'
---
layout: docs
---

# Utility Functions

Explore the utility functions provided by S3U.

## Listing Folders

A section about listing folders in your S3 buckets.

## Browsing Content

A section about browsing uploaded content.

## Downloading Files

A section about downloading files from S3.

## File Renaming

A section about renaming files in S3.
EOF

# Configuration page
cat > site/docs/pages/configuration/index.mdx << 'EOF'
---
layout: docs
---

# Configuration

Learn how to configure S3U for your specific needs.

## Configuration System

A section about the configuration system.

## Output Formats

A section about configuring output formats.

## Performance Options

A section about performance-related settings.

## File Management Options

A section about file management configuration options.
EOF

# Reference page
cat > site/docs/pages/reference/index.mdx << 'EOF'
---
layout: docs
---

# Reference

Technical reference for S3U.

## Command Line Options

A section listing all command line options.

## Troubleshooting

A section with common troubleshooting tips.

## FAQ

Frequently asked questions about S3U.
EOF

# Create vocs.config.ts
cat > site/vocs.config.ts << 'EOF'
import { defineConfig } from 'vocs'

export default defineConfig({
  title: 'S3U Documentation',
  description: 'Documentation for S3U - AWS S3 Upload Utility',
  
  sidebar: [
    {
      text: 'Getting Started',
      link: '/getting-started',
    },
    {
      text: 'Core Uploading',
      link: '/core-uploading',
    },
    {
      text: 'Utility Functions',
      link: '/utility-functions',
    },
    {
      text: 'Configuration',
      link: '/configuration',
    },
    {
      text: 'Reference',
      link: '/reference',
    },
  ],
  
  theme: {
    accentColor: {
      light: '#FF9900', // AWS orange color
      dark: '#FF9900',
    },
    variables: {
      fontFamily: {
        default: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
      }
    }
  },
  
  // Optional: Set up social media links
  socialLinks: [
    {
      icon: 'github',
      url: 'https://github.com/yourusername/s3u',
    },
  ],
})
EOF

# Create styles.css with AWS color theme
cat > site/docs/styles.css << 'EOF'
/* Custom styling for S3U documentation */
@import "tailwindcss";

:root {
  --aws-orange: #FF9900;
  --aws-blue: #232F3E;
  --aws-light-blue: #1A73E8;
}

:root.dark {
  --vocs-color-background: #121212;
}

.Vocs_H1 {
  color: var(--aws-orange);
  margin-bottom: 1.5rem;
}

.Vocs_H2 {
  border-bottom: 1px solid var(--aws-orange);
  padding-bottom: 0.5rem;
  margin-top: 2rem;
  margin-bottom: 1rem;
}

.Vocs_CodeBlock {
  border-left: 4px solid var(--aws-orange);
}

.Vocs_Button--accent {
  background-color: var(--aws-orange);
}

.Vocs_Button--accent:hover {
  background-color: #e68a00;
}
EOF

# Add package.json scripts
cat > site/package.json << 'EOF'
{
  "name": "s3u-docs",
  "version": "1.0.0",
  "scripts": {
    "docs:dev": "vocs dev",
    "docs:build": "vocs build",
    "docs:preview": "vocs preview"
  },
  "dependencies": {
    "vocs": "^1.0.0"
  }
}
EOF

echo "✅ S3U Documentation structure has been created!"
echo "To start the dev server:"
echo "  cd site"
echo "  npm install"
echo "  npm run docs:dev"
echo ""
echo "The documentation will be available at http://localhost:5173"