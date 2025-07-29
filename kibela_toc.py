#!/usr/bin/env python3
"""
Kibela Table of Contents Generator

This script generates or updates a table of contents for a Kibela page.
It supports depth control and dry-run mode for previewing changes.
"""

import argparse
import os
import re
import sys
import json
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup


class KibelaTOCGenerator:
    def __init__(self):
        self.token = os.getenv('KIBELA_TOKEN')
        self.team = os.getenv('KIBELA_TEAM')
        
        if not self.token or not self.team:
            raise ValueError(
                "KIBELA_TOKEN and KIBELA_TEAM environment variables are required.\n"
                "Please check your ~/.zshrc file."
            )
        
        self.api_base = f"https://{self.team}.kibe.la/api/v1"
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    def extract_note_id_from_url(self, url: str) -> str:
        """Extract note ID from Kibela URL."""
        parsed = urlparse(url)
        
        # Handle different URL formats
        if '/notes/' in parsed.path:
            # Format: https://team.kibe.la/notes/123 or https://team.kibela.com/notes/123
            note_id = parsed.path.split('/notes/')[-1]
        elif '/shared/' in parsed.path:
            # Format: https://team.kibe.la/shared/notes/123 or https://team.kibela.com/shared/notes/123
            note_id = parsed.path.split('/notes/')[-1]
        else:
            raise ValueError(f"Invalid Kibela URL format: {url}")
        
        # Remove any additional path segments or query parameters
        note_id = note_id.split('/')[0].split('?')[0]
        
        if not note_id.isdigit():
            raise ValueError(f"Could not extract valid note ID from URL: {url}")
        
        return note_id

    def get_note_content(self, note_id: str) -> Dict:
        """Fetch note content from Kibela API using GraphQL."""
        # Official Kibela API endpoint (from documentation)
        api_url = f"https://{self.team}.kibe.la/api/v1"
        
        # First, get the internal note ID from the URL-based note ID using noteFromPath
        note_url = f"https://{self.team}.kibe.la/notes/{note_id}"
        
        # GraphQL query to get the internal note ID from URL
        id_query = """
        query($path: String!) {
          noteFromPath(path: $path) {
            id
          }
        }
        """
        
        # Headers as specified in official documentation
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'KibelaTOCGenerator/1.0'
        }
        
        print(f"Getting internal note ID for URL note ID {note_id}...")
        print(f"Note URL: {note_url}")
        
        try:
            # First request: get internal note ID
            id_request_body = {
                "query": id_query,
                "variables": {"path": note_url}
            }
            
            response = requests.post(
                api_url,
                headers=headers,
                json=id_request_body
            )
            
            print(f"ID lookup response status: {response.status_code}")
            
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
            
            data = response.json()
            
            if 'errors' in data:
                raise Exception(f"GraphQL errors: {data['errors']}")
            
            if not data.get('data', {}).get('noteFromPath'):
                raise Exception("Note not found or not accessible")
            
            internal_note_id = data['data']['noteFromPath']['id']
            print(f"✅ Found internal note ID: {internal_note_id}")
            
            # Second request: get note content using internal ID
            content_query = """
            query($id: ID!) {
              note(id: $id) {
                id
                title
                content
                contentHtml
                publishedAt
                updatedAt
                author {
                  account
                  realName
                }
              }
            }
            """
            
            content_request_body = {
                "query": content_query,
                "variables": {"id": internal_note_id}
            }
            
            print(f"Fetching note content using internal ID...")
            
            response = requests.post(
                api_url,
                headers=headers,
                json=content_request_body
            )
            
            print(f"Content response status: {response.status_code}")
            
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
            
            data = response.json()
            
            if 'errors' in data:
                raise Exception(f"GraphQL errors: {data['errors']}")
            
            if not data.get('data', {}).get('note'):
                raise Exception("Note content not found")
            
            print("✅ Successfully fetched note content")
            note_data = data['data']['note']
            # Store the internal ID for later use in updates
            note_data['_internal_id'] = internal_note_id
            return note_data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch note {note_id}: {e}")

    def update_note_content(self, note_id: str, new_content: str, base_content: str) -> Dict:
        """Update note content via Kibela API using GraphQL."""
        # Official Kibela API endpoint (from documentation)
        api_url = f"https://{self.team}.kibe.la/api/v1"
        
        # GraphQL mutation to update note content (based on working kibela-to-kibela implementation)
        mutation = """
        mutation($input: UpdateNoteContentInput!) {
          updateNoteContent(input: $input) {
            clientMutationId
          }
        }
        """
        
        variables = {
            "input": {
                "id": note_id,
                "baseContent": base_content,
                "newContent": new_content,
                "touch": True
            }
        }
        
        # Headers as specified in official documentation
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'KibelaTOCGenerator/1.0'
        }
        
        # Request body as specified in official documentation
        request_body = {
            "query": mutation,
            "variables": variables
        }
        
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=request_body
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
            
            data = response.json()
            
            if 'errors' in data:
                raise Exception(f"GraphQL errors: {data['errors']}")
            
            if not data.get('data', {}).get('updateNoteContent'):
                raise Exception("Failed to update note")
            
            return data['data']['updateNoteContent']
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to update note {note_id}: {e}")

    def extract_headings(self, content: str, max_depth: int = 3) -> List[Dict]:
        """Extract headings from markdown content."""
        headings = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Match markdown headings (# ## ### etc.)
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
                
                if level <= max_depth:
                    # Generate anchor link
                    anchor = self.generate_anchor(text)
                    headings.append({
                        'level': level,
                        'text': text,
                        'anchor': anchor,
                        'line': line_num
                    })
        
        return headings

    def generate_anchor(self, text: str) -> str:
        """Generate anchor link from heading text."""
        # Remove markdown formatting
        text = re.sub(r'[*_`]', '', text)
        # Convert to lowercase and replace spaces/special chars with hyphens
        anchor = re.sub(r'[^\w\s-]', '', text.lower())
        anchor = re.sub(r'[\s_-]+', '-', anchor)
        anchor = anchor.strip('-')
        return anchor

    def generate_toc(self, headings: List[Dict]) -> str:
        """Generate table of contents markdown."""
        if not headings:
            return ""
        
        toc_lines = ["## 目次", ""]
        
        for heading in headings:
            indent = "  " * (heading['level'] - 1)
            link = f"[{heading['text']}](#{heading['anchor']})"
            toc_lines.append(f"{indent}- {link}")
        
        toc_lines.append("")  # Empty line after TOC
        return "\n".join(toc_lines)

    def find_existing_toc(self, content: str) -> Tuple[Optional[int], Optional[int]]:
        """Find existing TOC in content. Returns (start_line, end_line) or (None, None)."""
        lines = content.split('\n')
        
        toc_start = None
        toc_end = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for TOC header
            if line in ['## 目次', '## Table of Contents', '## TOC']:
                toc_start = i
                
                # Find the end of TOC (next heading or empty line followed by content)
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    
                    # End if we hit another heading at same or higher level
                    if re.match(r'^#{1,2}\s+', next_line) and not next_line.startswith('###'):
                        toc_end = j
                        break
                    
                    # End if we hit content after empty lines
                    if j > i + 1 and next_line and not next_line.startswith('-') and not next_line.startswith('  -'):
                        # Look back for the last TOC line
                        for k in range(j - 1, i, -1):
                            if lines[k].strip():
                                toc_end = k + 1
                                break
                        break
                
                # If no end found, assume TOC goes to end of section
                if toc_end is None:
                    for j in range(len(lines) - 1, i, -1):
                        if lines[j].strip():
                            toc_end = j + 1
                            break
                
                break
        
        return (toc_start, toc_end)

    def insert_or_update_toc(self, content: str, toc: str) -> str:
        """Insert new TOC or update existing one."""
        lines = content.split('\n')
        
        # Find existing TOC
        toc_start, toc_end = self.find_existing_toc(content)
        
        if toc_start is not None and toc_end is not None:
            # Replace existing TOC
            new_lines = lines[:toc_start] + toc.split('\n') + lines[toc_end:]
        else:
            # Insert TOC at the beginning (after title if present)
            insert_pos = 0
            
            # Skip title if present
            if lines and lines[0].startswith('# '):
                insert_pos = 1
                # Skip empty lines after title
                while insert_pos < len(lines) and not lines[insert_pos].strip():
                    insert_pos += 1
            
            new_lines = lines[:insert_pos] + [''] + toc.split('\n') + lines[insert_pos:]
        
        return '\n'.join(new_lines)

    def process_note(self, url: str, depth: int = 3, dry_run: bool = False) -> Dict:
        """Main processing function."""
        print(f"Processing Kibela URL: {url}")
        print(f"Depth: {depth}")
        print(f"Dry run: {dry_run}")
        print()
        
        # Extract note ID
        note_id = self.extract_note_id_from_url(url)
        print(f"Note ID: {note_id}")
        
        # Fetch note content
        note_data = self.get_note_content(note_id)
        original_content = note_data.get('content', '')
        title = note_data.get('title', '')
        
        print(f"Note title: {title}")
        print(f"Content length: {len(original_content)} characters")
        print()
        
        # Extract headings
        headings = self.extract_headings(original_content, depth)
        print(f"Found {len(headings)} headings (depth <= {depth}):")
        
        for heading in headings:
            indent = "  " * (heading['level'] - 1)
            print(f"{indent}H{heading['level']}: {heading['text']}")
        print()
        
        if not headings:
            print("No headings found. Nothing to do.")
            return {'success': True, 'message': 'No headings found'}
        
        # Generate TOC
        toc = self.generate_toc(headings)
        print("Generated TOC:")
        print(toc)
        print()
        
        # Insert or update TOC
        new_content = self.insert_or_update_toc(original_content, toc)
        
        if dry_run:
            print("DRY RUN - No changes made to the note.")
            print("\nPreview of updated content:")
            print("-" * 50)
            print(new_content[:1000] + ("..." if len(new_content) > 1000 else ""))
            print("-" * 50)
            return {'success': True, 'message': 'Dry run completed'}
        
        # Update note
        print("Updating note...")
        try:
            # Use the internal ID for updates
            internal_id = note_data.get('_internal_id', note_id)
            result = self.update_note_content(internal_id, new_content, original_content)
            print("✅ Note updated successfully!")
            return {'success': True, 'message': 'Note updated successfully', 'result': result}
        except Exception as e:
            print(f"❌ Failed to update note: {e}")
            return {'success': False, 'message': str(e)}


def main():
    parser = argparse.ArgumentParser(
        description='Generate or update table of contents for a Kibela page',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://team.kibela.com/notes/123
  %(prog)s https://team.kibela.com/notes/123 --depth 2
  %(prog)s https://team.kibela.com/notes/123 --depth 4 --dry-run
        """
    )
    
    parser.add_argument('url', help='Kibela page URL')
    parser.add_argument(
        '--depth', '-d',
        type=int,
        default=3,
        choices=range(1, 7),
        help='Maximum heading depth to include (1-6, default: 3)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without updating the note'
    )
    
    args = parser.parse_args()
    
    try:
        generator = KibelaTOCGenerator()
        result = generator.process_note(args.url, args.depth, args.dry_run)
        
        if result['success']:
            sys.exit(0)
        else:
            print(f"Error: {result['message']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
