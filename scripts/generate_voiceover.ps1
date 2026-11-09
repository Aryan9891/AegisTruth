# Generate Narration Audio Tracks for AegisTruth Demo Video

Add-Type -AssemblyName System.Speech
$audioDir = Join-Path $PSScriptRoot "audio"
if (-not (Test-Path $audioDir)) {
    New-Item -ItemType Directory -Path $audioDir -Force | Out-Null
}

$scenes = @(
    @{
        id = "scene_1"
        text = "Welcome to AegisTruth Sentinel, the multi-modal cognitive defense suite built to protect organizations from synthetic media threats, deepfakes, and adversarial AI attacks."
    },
    @{
        id = "scene_2"
        text = "Our Visual Forensics Studio uses Error Level Analysis, 2D Fourier spatial harmonics, and CMOS sensor noise correlation to detect diffusion artifacts from Midjourney and Stable Diffusion."
    },
    @{
        id = "scene_3"
        text = "The Temporal Video Sentinel inspects frame to frame optical flow continuity and Laplacian boundary edge flicker, exposing Sora, Kling, Runway, and FaceSwap generative video manipulations."
    },
    @{
        id = "scene_4"
        text = "In the Voice Clone Acoustic Lab, we analyze mel-spectrograms, pitch micro-jitter, and glottal pulse consistency to screen out synthetic voice clones from ElevenLabs and text to speech models."
    },
    @{
        id = "scene_5"
        text = "Cognitive Text Forensics evaluates perplexity and sentence burstiness, while the Automated Fact Sentinel extracts assertions to detect hallucinations and cross-sentence contradictions."
    },
    @{
        id = "scene_6"
        text = "For autonomous AI agents, our Zero-Trust Guard intercepts zero-width Unicode obfuscations and DAN jailbreaks, while the Tool Execution Firewall sandboxes and blocks destructive system calls."
    },
    @{
        id = "scene_7"
        text = "AegisTruth binds all forensic evaluations into immutable C2PA cryptographic provenance manifests, generating exportable court-admissible HTML certificates with SHA-256 digital seals."
    },
    @{
        id = "scene_8"
        text = "AegisTruth operates client-side in the browser or on local hardware, ensuring complete privacy with zero data leakage. Test the live platform at aryan9891.github.io/AegisTruth."
    }
)

$meta = @()

foreach ($sc in $scenes) {
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $synth.Rate = 0  # Natural conversational pace
    
    # Try selecting a clear natural English voice
    try {
        $synth.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Male, [System.Speech.Synthesis.VoiceAge]::Adult)
    } catch {}

    $wavPath = Join-Path $audioDir "$($sc.id).wav"
    $synth.SetOutputToWaveFile($wavPath)
    $synth.Speak($sc.text)
    $synth.Dispose()

    # Get duration using Shell.Application or audio length
    $file = Get-Item $wavPath
    # 16-bit 22050Hz or 44100Hz mono/stereo wav
    # Standard SAPI default is 22050Hz, 16bit, mono (44100 bytes/sec) or similar
    # Let's inspect length
    Write-Host "Generated $($sc.id).wav ($($file.Length) bytes)"
    
    $meta += @{
        id = $sc.id
        wav = $wavPath
        text = $sc.text
    }
}

Write-Host "All 8 voice narration tracks generated successfully."
