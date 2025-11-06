from google import genai
import json
from pathlib import Path
import datetime
import os

class GeminiTranscriber:
    def __init__(self, api_key=None):
        """
        Initialize the Gemini Transcriber
        
        Args:
            api_key: Your Google AI API key. If None, will use environment variable
        """
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"
    
    def transcribe_audio(self, file_path, enable_speaker_diarization=True):
        """
        Transcribe audio file with advanced features
        
        Args:
            file_path: Path to audio file
            enable_speaker_diarization: Whether to identify different speakers
            
        Returns:
            Dictionary containing transcript and metadata
        """
        print(f"Uploading file: {file_path}")
        
        try:
            # Upload the audio file
            myfile = self.client.files.upload(file=file_path)
            print("File uploaded successfully. Starting transcription...")
            
            # Build the prompt based on features
            if enable_speaker_diarization:
                prompt = self._get_detailed_prompt()
            else:
                prompt = self._get_basic_prompt()
            
            # Generate transcription
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt, myfile]
            )
            
            print("Transcription completed!")
            return self._parse_response(response.text, file_path)
            
        except Exception as e:
            print(f"Error during transcription: {e}")
            return None
    
    def _get_detailed_prompt(self):
        """Get detailed prompt for speaker diarization"""
        return """
        Please transcribe this audio recording with high accuracy and detail:

        REQUIREMENTS:
        1. SPEAKER IDENTIFICATION:
           - Identify each unique speaker consistently (Speaker 1, Speaker 2, etc.)
           - Use the same speaker labels throughout the entire recording
           - Note when speakers change

        2. TIMESTAMPING:
           - Provide timestamps at every speaker change [HH:MM:SS]
           - Add timestamps for major topic changes [approx. every 2-3 minutes]
           - Mark significant pauses [pause], overlapping speech [overlap], or inaudible sections [inaudible]

        3. FORMATTING:
           - Use clear paragraph breaks between different topics
           - Include important non-verbal cues: [laughs], [applause], [coughs] when relevant
           - Maintain proper punctuation and capitalization
           - Preserve technical terms or specific jargon accurately

        4. OUTPUT STRUCTURE:
           Start with metadata section, then the transcript.

        Format your response exactly like this:

        [METADATA]
        Total Speakers: [number]
        Audio Quality: [excellent/good/fair/poor]
        Key Topics: [list main topics discussed]

        [TRANSCRIPT]
        [00:00:00] Speaker 1: Welcome everyone to today's meeting. Let's start with the quarterly review.
        [00:00:15] Speaker 2: Thanks John. I'll begin with the sales numbers...
        [00:02:30] Speaker 1: [interrupting] Can you clarify those Q3 figures?
        [00:02:35] Speaker 2: Certainly. The Q3 numbers were...
        """
    
    def _get_basic_prompt(self):
        """Get basic prompt for simple transcription"""
        return """
        Please transcribe this audio recording accurately with timestamps at regular intervals.
        Include speaker changes when detectable and maintain proper formatting.
        """
    
    def _parse_response(self, response_text, file_path):
        """Parse the model response into structured data"""
        try:
            # Extract file info
            file_info = {
                'filename': Path(file_path).name,
                'file_size': f"{os.path.getsize(file_path) / (1024*1024):.2f} MB",
                'processed_at': datetime.datetime.now().isoformat()
            }
            
            # Parse structured response
            if '[METADATA]' in response_text and '[TRANSCRIPT]' in response_text:
                metadata_section = response_text.split('[METADATA]')[1].split('[TRANSCRIPT]')[0].strip()
                transcript_section = response_text.split('[TRANSCRIPT]')[1].strip()
                
                # Parse metadata
                metadata = {}
                for line in metadata_section.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
                
                return {
                    'file_info': file_info,
                    'metadata': metadata,
                    'transcript': transcript_section,
                    'raw_response': response_text
                }
            else:
                # Fallback for non-structured response
                return {
                    'file_info': file_info,
                    'metadata': {'Note': 'Auto-generated transcript'},
                    'transcript': response_text,
                    'raw_response': response_text
                }
                
        except Exception as e:
            print(f"Error parsing response: {e}")
            return {
                'file_info': file_info,
                'metadata': {'Error': 'Failed to parse structure'},
                'transcript': response_text,
                'raw_response': response_text
            }

class ExportManager:
    """Handle exporting transcripts to various formats"""
    
    @staticmethod
    def to_notion_markdown(transcript_data, output_path=None):
        """Export to Notion-compatible Markdown"""
        if output_path is None:
            output_path = f"transcript_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        content = f"""# Audio Transcript: {transcript_data['file_info']['filename']}

## Metadata
- **File**: {transcript_data['file_info']['filename']}
- **Size**: {transcript_data['file_info']['file_size']}
- **Processed**: {transcript_data['file_info']['processed_at']}
"""
        
        # Add metadata fields
        for key, value in transcript_data['metadata'].items():
            content += f"- **{key}**: {value}\n"
        
        content += f"""
---

## Transcript

{transcript_data['transcript']}

---
*Automatically generated using Gemini 2.5 Flash Transcription*
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Notion Markdown exported to: {output_path}")
        return output_path
    
    @staticmethod
    def to_google_docs_text(transcript_data, output_path=None):
        """Export to plain text for Google Docs"""
        if output_path is None:
            output_path = f"transcript_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Simple text format
        content = f"TRANSCRIPT: {transcript_data['file_info']['filename']}\n"
        content += f"Generated: {transcript_data['file_info']['processed_at']}\n"
        content += "="*50 + "\n\n"
        content += transcript_data['transcript']
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Google Docs text exported to: {output_path}")
        return output_path
    
    @staticmethod
    def to_json(transcript_data, output_path=None):
        """Export to JSON format"""
        if output_path is None:
            output_path = f"transcript_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
        print(f"JSON exported to: {output_path}")
        return output_path

def main():
    """Main function to run the transcription workflow"""
    
    # Initialize the transcriber
    transcriber = GeminiTranscriber()
    
    # File to transcribe
    audio_file = "path/to/your/audio/file.mp3"  # Change this to your file path
    
    if not os.path.exists(audio_file):
        print(f"Error: File not found - {audio_file}")
        print("Please update the 'audio_file' variable with your actual file path")
        return
    
    # Perform transcription
    print("=== Gemini 2.5 Flash Transcription ===")
    result = transcriber.transcribe_audio(audio_file, enable_speaker_diarization=True)
    
    if result:
        # Export to various formats
        export_manager = ExportManager()
        
        # Export to Notion format
        notion_file = export_manager.to_notion_markdown(result)
        
        # Export to Google Docs format
        docs_file = export_manager.to_google_docs_text(result)
        
        # Export to JSON
        json_file = export_manager.to_json(result)
        
        # Print summary
        print("\n=== TRANSCRIPTION COMPLETE ===")
        print(f"Input file: {result['file_info']['filename']}")
        print(f"Speakers identified: {result['metadata'].get('Total Speakers', 'Unknown')}")
        print(f"Audio quality: {result['metadata'].get('Audio Quality', 'Unknown')}")
        print(f"\nFirst 500 characters of transcript:")
        print(result['transcript'][:500] + "...")
        
        print(f"\nExported files:")
        print(f"- Notion: {notion_file}")
        print(f"- Google Docs: {docs_file}")
        print(f"- JSON: {json_file}")
    
    else:
        print("Transcription failed. Please check the error messages above.")

def batch_transcribe_directory(input_directory, output_directory="transcripts"):
    """
    Batch transcribe all audio files in a directory
    """
    Path(output_directory).mkdir(exist_ok=True)
    transcriber = GeminiTranscriber()
    
    audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg'}
    
    for file_path in Path(input_directory).iterdir():
        if file_path.suffix.lower() in audio_extensions:
            print(f"\n{'='*50}")
            print(f"Processing: {file_path.name}")
            print(f"{'='*50}")
            
            try:
                result = transcriber.transcribe_audio(str(file_path))
                
                if result:
                    # Save with original filename
                    base_name = file_path.stem
                    ExportManager.to_notion_markdown(
                        result, 
                        f"{output_directory}/{base_name}_transcript.md"
                    )
                    
            except Exception as e:
                print(f"Error processing {file_path.name}: {e}")

# Example usage
if __name__ == "__main__":
    # Option 1: Transcribe a single file
    main()
    
    # Option 2: Batch transcribe a directory
    # batch_transcribe_directory("/path/to/your/audio/files")
