Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

$form = New-Object System.Windows.Forms.Form
$form.Text = "Submit AutoClicker Form Test"
$form.Width = 520
$form.Height = 250
$form.StartPosition = "CenterScreen"
$form.TopMost = $true

$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Text = "Auto-Clicker Desktop Test"
$titleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 13, [System.Drawing.FontStyle]::Bold)
$titleLabel.AutoSize = $true
$titleLabel.Location = New-Object System.Drawing.Point(20, 20)
$form.Controls.Add($titleLabel)

$questionLabel = New-Object System.Windows.Forms.Label
$questionLabel.Text = "Do you approve this automation test?"
$questionLabel.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$questionLabel.AutoSize = $true
$questionLabel.Location = New-Object System.Drawing.Point(20, 60)
$form.Controls.Add($questionLabel)

$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Text = "Waiting for Submit click..."
$statusLabel.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$statusLabel.AutoSize = $true
$statusLabel.Location = New-Object System.Drawing.Point(20, 95)
$statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(51, 65, 85)
$form.Controls.Add($statusLabel)

$submitButton = New-Object System.Windows.Forms.Button
$submitButton.Text = "Submit"
$submitButton.Width = 120
$submitButton.Height = 35
$submitButton.Location = New-Object System.Drawing.Point(20, 140)
$submitButton.Enabled = $false
$form.Controls.Add($submitButton)

$closeButton = New-Object System.Windows.Forms.Button
$closeButton.Text = "Close"
$closeButton.Width = 100
$closeButton.Height = 35
$closeButton.Location = New-Object System.Drawing.Point(150, 140)
$closeButton.Add_Click({ $form.Close() })
$form.Controls.Add($closeButton)

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 2500
$timer.Add_Tick({
    $timer.Stop()
    $submitButton.Enabled = $true
    $statusLabel.Text = "Submit enabled. Bot should click it automatically."
})
$timer.Start()

$submitButton.Add_Click({
    $timestamp = [DateTime]::Now.ToString("HH:mm:ss")
    $statusLabel.Text = "Submit clicked at $timestamp. Test succeeded."
    $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(22, 101, 52)
    $submitButton.Enabled = $false
    Write-Host "submit_clicked_at=$timestamp"
})

[void]$form.ShowDialog()
