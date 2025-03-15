import { defineConfig } from 'vocs'

export default defineConfig({
  title: 's3u Documentation',
  description: 'Documentation for s3u - AWS S3 Upload Utility',
  
  sidebar: [
    {
      text: 'Getting Started',
      // link: '/getting-started',
      // Explicitly make sections not collapsible
      collapsed: false,
      collapsible: false,
      items: [
        { text: 'Installation', link: '/getting-started#installation' },
        { text: 'AWS Configuration', link: '/getting-started#aws-configuration' },
        { text: 'Setup', link: '/getting-started#setup' },
      ]
    },
    {
      text: 'Core Uploading',
      // link: '/core-uploading',
      collapsed: false,
      collapsible: false,
      items: [
        { text: 'Interactive Upload Process', link: '/core-uploading#interactive-upload-process' },
        { text: 'Media Optimization', link: '/core-uploading#media-optimization' },
        { text: 'Concurrent Uploads', link: '/core-uploading#concurrent-uploads' },
        { text: 'Subfolder Handling', link: '/core-uploading#subfolder-handling' },
        { text: 'Progress Tracking', link: '/core-uploading#progress-tracking' },
        { text: 'Post-Upload Actions', link: '/core-uploading#post-upload-actions' },
        { text: 'Advanced Options', link: '/core-uploading#advanced-options' },
      ]
    },
    {
      text: 'Utility Functions',
      // link: '/utility-functions',
      collapsed: false,
      collapsible: false,
      items: [
        { text: 'Listing Folders', link: '/utility-functions#listing-folders' },
        { text: 'Browsing Content', link: '/utility-functions#browsing-content' },
        { text: 'Downloading Files', link: '/utility-functions#downloading-files' },
        { text: 'File Renaming', link: '/utility-functions#file-renaming' },
        { text: 'File Selection', link: '/utility-functions#file-selection-and-filtering' },
        { text: 'Use Cases & Examples', link: '/utility-functions#use-cases-and-examples' },
      ]
    },
    {
      text: 'Configuration',
      // link: '/configuration',
      collapsed: false,
      collapsible: false,
      items: [
        { text: 'Configuration System', link: '/configuration#configuration-system' },
        { text: 'Output Formats', link: '/configuration#output-formats' },
        { text: 'Performance Options', link: '/configuration#performance-options' },
        { text: 'Media Optimization', link: '/configuration#media-optimization-options' },
        { text: 'File Management', link: '/configuration#file-management-options' },
        { text: 'AWS Configuration', link: '/configuration#aws-configuration-options' },
        { text: 'Example Configurations', link: '/configuration#example-configurations' },
      ]
    },
    {
      text: 'Reference',
      // link: '/reference',
      collapsed: false,
      collapsible: false,
      items: [
        { text: 'Command Line Options', link: '/reference#command-line-options' },
        { text: 'Troubleshooting', link: '/reference#troubleshooting' },
        { text: 'FAQ', link: '/reference#faq' },
      ]
    },
  ],
  
  // Global sidebar settings
  defaultSidebarCollapsed: false,
  
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
  
  // Add edit links to GitHub
  editLink: {
    pattern: 'https://github.com/yourusername/s3u-docs/edit/main/docs/pages/:path',
    text: 'Edit this page on GitHub'
  },
  
  // Improve site metadata for SEO
  head: {
    meta: [
      { name: 'keywords', content: 'aws, s3, upload, cloudfront, file management, image optimization' },
      { name: 'author', content: 'Your Name' },
    ],
    // Favicon
    link: [
      { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
    ]
  }
})