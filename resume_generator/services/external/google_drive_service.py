"""
Google Drive integration for monitoring Excel files and creating Google Docs
"""
import os
import io
import re
from datetime import datetime
from typing import List, Dict, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from google.auth.transport.requests import Request
import pandas as pd
from django.conf import settings


class GoogleDriveService:
    """Service to interact with Google Drive API"""
    
    def __init__(self):
        """Initialize Google Drive API service"""
        self.credentials_file = settings.GOOGLE_DRIVE_CREDENTIALS_FILE
        self.scopes = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/documents'
        ]
        self.drive_service = None
        self.docs_service = None
        
        if self.credentials_file and os.path.exists(self.credentials_file):
            self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Google Drive and Docs API services"""
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=self.scopes
            )
            
            self.drive_service = build('drive', 'v3', credentials=creds)
            self.docs_service = build('docs', 'v1', credentials=creds)
        
        except Exception as e:
            raise Exception(f"Error initializing Google Drive service: {str(e)}")
    
    def read_excel_from_drive(self, file_id: str) -> List[Dict]:
        """
        Read Excel file from Google Drive (supports Google Sheets)
        
        Args:
            file_id: Google Drive file ID
        
        Returns:
            List of job application dictionaries
        """
        if not self.drive_service:
            raise Exception("Google Drive service not initialized")
        
        try:
            # Export as Excel format (for Google Sheets)
            request = self.drive_service.files().export_media(
                fileId=file_id,
                mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_content.seek(0)
            
            # Read Excel file
            df = pd.read_excel(file_content)
            
            # Normalize column names
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # At least one of job_url or job_description must be present
            if 'job_url' not in df.columns and 'job_description' not in df.columns:
                raise ValueError("Excel file must contain either 'job_url' or 'job_description' column")
            
            # Fill missing columns with defaults
            if 'unique_id' not in df.columns:
                df['unique_id'] = ''
            if 'job_url' not in df.columns:
                df['job_url'] = ''
            if 'job_description' not in df.columns:
                df['job_description'] = ''
            if 'additional_instructions' not in df.columns:
                df['additional_instructions'] = ''
            if 'generate_resume' not in df.columns:
                df['generate_resume'] = 'yes'
            if 'generate_cover' not in df.columns:
                df['generate_cover'] = 'yes'
            if 'generate_new_resume' not in df.columns:
                df['generate_new_resume'] = 'yes'
            if 'resume_generated' not in df.columns:
                df['resume_generated'] = 'no'
            if 'cover_letter_generated' not in df.columns:
                df['cover_letter_generated'] = 'no'
            if 'recommendations' not in df.columns:
                df['recommendations'] = ''
            if 'company_name' not in df.columns:
                df['company_name'] = ''
            if 'google_doc_url' not in df.columns:
                df['google_doc_url'] = ''
            
            # Convert to list of dictionaries
            job_applications = []
            for idx, row in df.iterrows():
                # Skip if both job_url and job_description are empty
                job_url = str(row['job_url']).strip() if not pd.isna(row['job_url']) else ''
                job_desc = str(row['job_description']).strip() if not pd.isna(row['job_description']) else ''
                
                if not job_url and not job_desc:
                    continue
                
                job_app = {
                    'unique_id': str(row['unique_id']) if not pd.isna(row['unique_id']) and str(row['unique_id']).strip() else '',
                    'job_url': job_url,
                    'job_description': job_desc,
                    'additional_instructions': str(row['additional_instructions']) if not pd.isna(row['additional_instructions']) else '',
                    'generate_resume': str(row['generate_resume']).lower() in ['yes', 'true', '1', 'y'],
                    'generate_cover_letter': str(row['generate_cover']).lower() in ['yes', 'true', '1', 'y'],
                    'generate_new_resume': str(row['generate_new_resume']).lower() in ['yes', 'true', '1', 'y'],
                    'resume_generated': str(row['resume_generated']).lower() in ['yes', 'true', '1', 'y'],
                    'cover_letter_generated': str(row['cover_letter_generated']).lower() in ['yes', 'true', '1', 'y'],
                    'company_name': str(row['company_name']) if not pd.isna(row['company_name']) else '',
                    'excel_row_index': int(idx) + 2,
                }
                job_applications.append(job_app)
            
            return job_applications
        
        except Exception as e:
            raise Exception(f"Error reading Excel from Google Drive: {str(e)}")
    
    def update_excel_in_drive(self, file_id: str, row_index: int,
                             unique_id: str = None,
                             resume_generated: bool = None,
                             cover_letter_generated: bool = None,
                             recommendations: str = None,
                             company_name: str = None,
                             google_doc_url: str = None) -> bool:
        """
        Update Excel file in Google Drive with generation status
        
        Args:
            file_id: Google Drive file ID
            row_index: Excel row number (1-indexed, including header)
            unique_id: Unique identifier for the row
            resume_generated: Whether resume was generated
            cover_letter_generated: Whether cover letter was generated
            recommendations: AI recommendations text
            company_name: Extracted company name
            google_doc_url: URL to the generated Google Doc
        
        Returns:
            True if successful
        """
        if not self.drive_service:
            raise Exception("Google Drive service not initialized")
        
        try:
            # Download current file (use export for Google Sheets)
            request = self.drive_service.files().export_media(
                fileId=file_id,
                mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_content.seek(0)
            
            # Read Excel
            df = pd.read_excel(file_content)
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Add columns if they don't exist and ensure they're object type (string)
            if 'unique_id' not in df.columns:
                df['unique_id'] = ''
            else:
                df['unique_id'] = df['unique_id'].astype(str).replace('nan', '')
            
            if 'resume_generated' not in df.columns:
                df['resume_generated'] = 'no'
            else:
                df['resume_generated'] = df['resume_generated'].astype(str)
                
            if 'cover_letter_generated' not in df.columns:
                df['cover_letter_generated'] = 'no'
            else:
                df['cover_letter_generated'] = df['cover_letter_generated'].astype(str)
                
            if 'recommendations' not in df.columns:
                df['recommendations'] = ''
            else:
                df['recommendations'] = df['recommendations'].astype(str).replace('nan', '')
                
            if 'company_name' not in df.columns:
                df['company_name'] = ''
            else:
                df['company_name'] = df['company_name'].astype(str).replace('nan', '')
                
            if 'google_doc_url' not in df.columns:
                df['google_doc_url'] = ''
            else:
                df['google_doc_url'] = df['google_doc_url'].astype(str).replace('nan', '')
            
            # Update row
            df_index = row_index - 2
            
            if df_index < 0 or df_index >= len(df):
                raise ValueError(f"Invalid row index: {row_index}")
            
            if unique_id is not None:
                df.at[df_index, 'unique_id'] = unique_id
            if resume_generated is not None:
                df.at[df_index, 'resume_generated'] = 'yes' if resume_generated else 'no'
            if cover_letter_generated is not None:
                df.at[df_index, 'cover_letter_generated'] = 'yes' if cover_letter_generated else 'no'
            if recommendations is not None:
                df.at[df_index, 'recommendations'] = recommendations
            if company_name is not None:
                df.at[df_index, 'company_name'] = company_name
            if google_doc_url is not None:
                df.at[df_index, 'google_doc_url'] = google_doc_url
            
            # Save to BytesIO
            output = io.BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)
            
            # Upload back to Drive (convert Excel to Google Sheets)
            media = MediaIoBaseUpload(
                output, 
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                resumable=True
            )
            
            # Update the file (Google Drive will automatically convert Excel to Sheets)
            self.drive_service.files().update(
                fileId=file_id,
                media_body=media,
                supportsAllDrives=True
            ).execute()
            
            return True
        
        except Exception as e:
            raise Exception(f"Error updating Excel in Google Drive: {str(e)}")
    
    def create_google_doc(self, folder_id: str, doc_title: str,
                         resume_content: str, cover_letter_content: str) -> Dict:
        """
        Create a Google Doc with resume and cover letter
        
        Args:
            folder_id: Google Drive folder ID
            doc_title: Document title (company name)
            resume_content: Resume text
            cover_letter_content: Cover letter text
        
        Returns:
            Dictionary with doc_id and doc_url
        """
        if not self.docs_service or not self.drive_service:
            raise Exception("Google services not initialized")
        
        try:
            # Create the document
            doc = self.docs_service.documents().create(body={'title': doc_title}).execute()
            doc_id = doc['documentId']
            
            # Build content with formatting
            requests = []
            
            # Cover Letter Section
            requests.append({
                'insertText': {
                    'location': {'index': 1},
                    'text': f"COVER LETTER\n\n{cover_letter_content}\n\n"
                }
            })
            
            # Page break
            requests.append({
                'insertText': {
                    'location': {'index': 1},
                    'text': "\n--- PAGE BREAK ---\n\n"
                }
            })
            
            # Resume Section
            requests.append({
                'insertText': {
                    'location': {'index': 1},
                    'text': f"RESUME\n\n{resume_content}"
                }
            })
            
            # Apply formatting
            self.docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
            
            # Move to folder
            self.drive_service.files().update(
                fileId=doc_id,
                addParents=folder_id,
                fields='id, parents'
            ).execute()
            
            # Get shareable link
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            
            return {
                'doc_id': doc_id,
                'doc_url': doc_url
            }
        
        except Exception as e:
            raise Exception(f"Error creating Google Doc: {str(e)}")
    
    def update_google_doc(self, doc_id: str, resume_content: str, cover_letter_content: str) -> Dict:
        """
        Update an existing Google Doc with new resume and cover letter content
        
        Args:
            doc_id: Google Doc ID to update
            resume_content: Resume text
            cover_letter_content: Cover letter text
        
        Returns:
            Dictionary with doc_id and doc_url
        """
        if not self.docs_service:
            raise Exception("Google Docs service not initialized")
        
        try:
            # Get current document to find the end index
            doc = self.docs_service.documents().get(documentId=doc_id).execute()
            content = doc.get('body').get('content')
            end_index = content[-1].get('endIndex', 1)
            
            # Clear existing content and insert new content
            requests = []
            
            # Delete all existing content (keep index 1 as it's required)
            if end_index > 2:
                requests.append({
                    'deleteContentRange': {
                        'range': {
                            'startIndex': 1,
                            'endIndex': end_index - 1
                        }
                    }
                })
            
            # Insert new content
            # Cover Letter Section
            requests.append({
                'insertText': {
                    'location': {'index': 1},
                    'text': f"COVER LETTER\n\n{cover_letter_content}\n\n"
                }
            })
            
            # Page break
            requests.append({
                'insertText': {
                    'location': {'index': 1},
                    'text': "\n--- PAGE BREAK ---\n\n"
                }
            })
            
            # Resume Section
            requests.append({
                'insertText': {
                    'location': {'index': 1},
                    'text': f"RESUME\n\n{resume_content}"
                }
            })
            
            # Apply updates
            self.docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
            
            # Get shareable link
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            
            return {
                'doc_id': doc_id,
                'doc_url': doc_url
            }
        
        except Exception as e:
            raise Exception(f"Error updating Google Doc: {str(e)}")
    
    def get_file_metadata(self, file_id: str) -> Dict:
        """Get file metadata including modification time"""
        if not self.drive_service:
            raise Exception("Google Drive service not initialized")
        
        try:
            file = self.drive_service.files().get(
                fileId=file_id,
                fields='id, name, modifiedTime'
            ).execute()
            
            return {
                'id': file['id'],
                'name': file['name'],
                'modified_time': file['modifiedTime']
            }
        
        except Exception as e:
            raise Exception(f"Error getting file metadata: {str(e)}")
    
    @staticmethod
    def extract_company_name(job_description: str, job_url: str) -> str:
        """
        Extract company name from job description or URL
        
        Args:
            job_description: Job description text
            job_url: Job posting URL
        
        Returns:
            Company name
        """
        # Try to extract from URL first
        url_patterns = [
            r'linkedin\.com/company/([^/]+)',
            r'jobs\.([^./]+)\.',
            r'careers\.([^./]+)\.',
            r'([^./]+)\.com/careers',
            r'([^./]+)\.com/jobs',
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, job_url)
            if match:
                company = match.group(1).replace('-', ' ').title()
                if len(company) > 3:
                    return company
        
        # Try to extract from job description
        # Look for common patterns like "Company Name is hiring" or "Join Company Name"
        patterns = [
            r'(?:at|join|for)\s+([A-Z][a-zA-Z\s&]+?)(?:\s+is|\s+are|\s+-|\s+in|\.|,)',
            r'([A-Z][a-zA-Z\s&]+?)\s+(?:is hiring|seeks|looking for)',
            r'Company:\s*([A-Z][a-zA-Z\s&]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, job_description[:500])
            if match:
                company = match.group(1).strip()
                if 3 < len(company) < 50:
                    return company
        
        # Fallback
        return "Company"
    
    def setup_excel_headers(self, file_id: str) -> bool:
        """
        Set up the correct column headers in the Google Sheet
        
        Args:
            file_id: Google Drive file ID
        
        Returns:
            True if successful
        """
        if not self.drive_service:
            raise Exception("Google Drive service not initialized")
        
        try:
            # Download as Excel format (export from Google Sheets)
            request = self.drive_service.files().export_media(
                fileId=file_id,
                mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_content.seek(0)
            
            # Read Excel file
            df = pd.read_excel(file_content)
            
            # Define correct headers
            correct_headers = [
                'Unique ID',
                'Job URL',
                'Job Description',
                'Additional Instructions',
                'Generate Resume',
                'Generate Cover',
                'Generate New Resume',
                'Resume Generated',
                'Cover Letter Generated',
                'Recommendations',
                'Company Name',
                'Google Doc URL'
            ]
            
            # If sheet is empty or has wrong headers, set correct ones
            if len(df.columns) < len(correct_headers) or df.empty:
                # Create new DataFrame with correct headers
                new_df = pd.DataFrame(columns=correct_headers)
                
                # Try to preserve existing data if any
                if not df.empty:
                    for idx, row in df.iterrows():
                        new_df = pd.concat([new_df, pd.DataFrame([row.to_dict()])], ignore_index=True)
            else:
                # Just rename the headers
                new_df = df.copy()
                for i, header in enumerate(correct_headers):
                    if i < len(new_df.columns):
                        new_df.columns.values[i] = header
            
            # Save back to Excel format
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                new_df.to_excel(writer, index=False, sheet_name='Sheet1')
            output.seek(0)
            
            # Upload back to Drive as Google Sheets
            media = MediaIoBaseUpload(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                resumable=True
            )
            self.drive_service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            
            return True
        
        except Exception as e:
            raise Exception(f"Error setting up Excel headers: {str(e)}")
