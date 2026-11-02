using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

namespace AegisAI.Installer
{
    public class InstallerForm : Form
    {
        private ProgressBar progressBar;
        private Label titleLabel;
        private Label subtitleLabel;
        private Label statusLabel;
        private Label percentLabel;
        private Panel headerPanel;
        private Button cancelButton;

        private string installDir;

        [DllImport("shell32.dll", SetLastError = true)]
        private static extern int SetCurrentProcessExplicitAppUserModelID([MarshalAs(UnmanagedType.LPWStr)] string AppID);

        [STAThread]
        public static int Main(string[] args)
        {
            try
            {
                SetCurrentProcessExplicitAppUserModelID("AegisAI.Installer.2026");
            }
            catch { }

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            bool silent = false;
            bool uninstall = false;
            string customDir = null;

            foreach (string arg in args)
            {
                if (arg.Equals("/silent", StringComparison.OrdinalIgnoreCase) || arg.Equals("/quiet", StringComparison.OrdinalIgnoreCase))
                    silent = true;
                else if (arg.Equals("/uninstall", StringComparison.OrdinalIgnoreCase))
                    uninstall = true;
                else if (arg.StartsWith("/dir=", StringComparison.OrdinalIgnoreCase))
                    customDir = arg.Substring(5).Trim('"');
            }

            string targetDir = customDir;
            if (string.IsNullOrEmpty(targetDir))
            {
                targetDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "AegisAI");
            }

            if (uninstall)
            {
                return PerformUninstall(targetDir, silent);
            }

            if (silent)
            {
                return PerformSilentInstall(targetDir);
            }

            InstallerForm form = new InstallerForm(targetDir);
            Application.Run(form);
            return 0;
        }

        public InstallerForm(string targetDir)
        {
            this.installDir = targetDir;

            // Form properties
            this.Text = "Aegis AI - One-Click Installer";
            this.Size = new Size(540, 340);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = true;
            this.BackColor = Color.FromArgb(11, 15, 25);
            this.ForeColor = Color.FromArgb(241, 245, 249);
            this.Font = new Font("Segoe UI", 9F, FontStyle.Regular, GraphicsUnit.Point);

            InitializeUI();

            this.Load += (s, e) =>
            {
                Thread worker = new Thread(RunInstallProcess);
                worker.IsBackground = true;
                worker.Start();
            };
        }

        private void InitializeUI()
        {
            // Header panel
            headerPanel = new Panel();
            headerPanel.Dock = DockStyle.Top;
            headerPanel.Height = 85;
            headerPanel.BackColor = Color.FromArgb(14, 21, 38);
            headerPanel.Padding = new Padding(20, 16, 20, 16);

            titleLabel = new Label();
            titleLabel.Text = "🛡️ Aegis AI - مثبت ويندوز التلقائي";
            titleLabel.Font = new Font("Segoe UI", 13F, FontStyle.Bold);
            titleLabel.ForeColor = Color.FromArgb(56, 189, 248);
            titleLabel.AutoSize = true;
            titleLabel.Location = new Point(18, 14);

            subtitleLabel = new Label();
            subtitleLabel.Text = "The Autonomous, Local-First Windows AI Companion (One-Click Setup)";
            subtitleLabel.Font = new Font("Segoe UI", 8.5F);
            subtitleLabel.ForeColor = Color.FromArgb(148, 163, 184);
            subtitleLabel.AutoSize = true;
            subtitleLabel.Location = new Point(20, 44);

            headerPanel.Controls.Add(titleLabel);
            headerPanel.Controls.Add(subtitleLabel);

            // Status & Details
            statusLabel = new Label();
            statusLabel.Text = "جاري تهيئة عملية التثبيت (Preparing setup)...";
            statusLabel.Font = new Font("Segoe UI", 9F, FontStyle.Regular);
            statusLabel.ForeColor = Color.FromArgb(203, 213, 225);
            statusLabel.Location = new Point(24, 115);
            statusLabel.Size = new Size(400, 24);

            percentLabel = new Label();
            percentLabel.Text = "0%";
            percentLabel.Font = new Font("Segoe UI", 9F, FontStyle.Bold);
            percentLabel.ForeColor = Color.FromArgb(56, 189, 248);
            percentLabel.Location = new Point(440, 115);
            percentLabel.Size = new Size(60, 24);
            percentLabel.TextAlign = ContentAlignment.TopRight;

            // Progress Bar
            progressBar = new ProgressBar();
            progressBar.Location = new Point(24, 145);
            progressBar.Size = new Size(476, 22);
            progressBar.Style = ProgressBarStyle.Continuous;
            progressBar.Minimum = 0;
            progressBar.Maximum = 100;
            progressBar.Value = 0;

            // Target destination note
            Label pathLabel = new Label();
            pathLabel.Text = "مسار التثبيت: " + installDir;
            pathLabel.Font = new Font("Segoe UI", 7.5F);
            pathLabel.ForeColor = Color.FromArgb(100, 116, 139);
            pathLabel.Location = new Point(24, 180);
            pathLabel.Size = new Size(476, 36);

            // Cancel Button
            cancelButton = new Button();
            cancelButton.Text = "إلغاء (Cancel)";
            cancelButton.Location = new Point(390, 245);
            cancelButton.Size = new Size(110, 30);
            cancelButton.BackColor = Color.FromArgb(30, 41, 59);
            cancelButton.ForeColor = Color.FromArgb(241, 245, 249);
            cancelButton.FlatStyle = FlatStyle.Flat;
            cancelButton.FlatAppearance.BorderColor = Color.FromArgb(51, 65, 85);
            cancelButton.Click += (s, e) => this.Close();

            this.Controls.Add(headerPanel);
            this.Controls.Add(statusLabel);
            this.Controls.Add(percentLabel);
            this.Controls.Add(progressBar);
            this.Controls.Add(pathLabel);
            this.Controls.Add(cancelButton);
        }

        private void UpdateProgress(int percent, string status)
        {
            if (this.InvokeRequired)
            {
                this.BeginInvoke(new Action(() => UpdateProgress(percent, status)));
                return;
            }

            if (percent >= 0 && percent <= 100)
            {
                progressBar.Value = percent;
                percentLabel.Text = percent + "%";
            }
            if (!string.IsNullOrEmpty(status))
            {
                statusLabel.Text = status;
            }
        }

        private void RunInstallProcess()
        {
            try
            {
                Thread.Sleep(400); // Visual pacing

                UpdateProgress(10, "إنهاء العمليات السابقة إن وجدت...");
                TerminateExistingProcesses();

                UpdateProgress(25, "استخراج ملفات التطبيق والمكتبات...");
                Directory.CreateDirectory(installDir);

                ExtractEmbeddedPackage(installDir, (progress) =>
                {
                    int scaled = 25 + (int)(progress * 0.45); // 25% -> 70%
                    UpdateProgress(scaled, "جاري استخراج حزم Aegis AI...");
                });

                UpdateProgress(75, "إنشاء اختصار سطح المكتب...");
                CreateDesktopShortcut(installDir);

                UpdateProgress(85, "إنشاء اختصار قائمة ابدأ...");
                CreateStartMenuShortcut(installDir);

                UpdateProgress(92, "تسجيل التطبيق في نظام ويندوز...");
                RegisterWindowsUninstall(installDir);

                // Copy self for uninstallation
                try
                {
                    string currentExe = Assembly.GetExecutingAssembly().Location;
                    string destExe = Path.Combine(installDir, "AegisAI-Setup.exe");
                    if (!string.Equals(currentExe, destExe, StringComparison.OrdinalIgnoreCase))
                    {
                        File.Copy(currentExe, destExe, true);
                    }
                }
                catch { }

                UpdateProgress(100, "✓ تم التثبيت بنجاح! جاري تشغيل Aegis AI...");
                Thread.Sleep(1000);

                // Launch Aegis AI
                LaunchApplication(installDir);

                this.BeginInvoke(new Action(() => this.Close()));
            }
            catch (Exception ex)
            {
                UpdateProgress(progressBar.Value, "خطأ أثناء التثبيت: " + ex.Message);
                MessageBox.Show("حدث خطأ أثناء تثبيت Aegis AI:\n" + ex.Message, "فشل التثبيت", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private static void TerminateExistingProcesses()
        {
            try
            {
                Process[] procs = Process.GetProcessesByName("AegisAI");
                foreach (var p in procs)
                {
                    try { p.Kill(); p.WaitForExit(1500); } catch { }
                }
            }
            catch { }
        }

        private static void ExtractEmbeddedPackage(string targetDir, Action<double> onProgress)
        {
            Assembly asm = Assembly.GetExecutingAssembly();
            using (Stream stream = asm.GetManifestResourceStream("AegisPackage"))
            {
                if (stream == null)
                {
                    throw new InvalidOperationException("Embedded package resource 'AegisPackage' was not found in this installer assembly.");
                }

                using (ZipArchive archive = new ZipArchive(stream, ZipArchiveMode.Read))
                {
                    int total = archive.Entries.Count;
                    int count = 0;

                    foreach (ZipArchiveEntry entry in archive.Entries)
                    {
                        count++;
                        string destPath = Path.GetFullPath(Path.Combine(targetDir, entry.FullName));

                        // Security check against directory traversal
                        if (!destPath.StartsWith(targetDir, StringComparison.OrdinalIgnoreCase))
                            continue;

                        if (string.IsNullOrEmpty(entry.Name))
                        {
                            Directory.CreateDirectory(destPath);
                        }
                        else
                        {
                            string parentDir = Path.GetDirectoryName(destPath);
                            if (!string.IsNullOrEmpty(parentDir))
                                Directory.CreateDirectory(parentDir);

                            entry.ExtractToFile(destPath, true);
                        }

                        if (onProgress != null && total > 0)
                        {
                            onProgress((double)count / total);
                        }
                    }
                }
            }
        }

        private static void CreateDesktopShortcut(string appDir)
        {
            try
            {
                string desktop = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
                string shortcutPath = Path.Combine(desktop, "Aegis AI.lnk");
                CreateShortcut(shortcutPath, appDir);
            }
            catch { }
        }

        private static void CreateStartMenuShortcut(string appDir)
        {
            try
            {
                string startMenu = Environment.GetFolderPath(Environment.SpecialFolder.Programs);
                string shortcutPath = Path.Combine(startMenu, "Aegis AI.lnk");
                CreateShortcut(shortcutPath, appDir);
            }
            catch { }
        }

        private static void CreateShortcut(string shortcutPath, string appDir)
        {
            string exePath = Path.Combine(appDir, "AegisAI.exe");
            if (!File.Exists(exePath))
            {
                exePath = Path.Combine(appDir, "run.bat");
            }
            string iconPath = Path.Combine(appDir, "assets", "icon.ico");

            Type shellType = Type.GetTypeFromProgID("WScript.Shell");
            if (shellType == null) return;

            dynamic shell = Activator.CreateInstance(shellType);
            dynamic shortcut = shell.CreateShortcut(shortcutPath);
            shortcut.TargetPath = exePath;
            shortcut.WorkingDirectory = appDir;
            if (File.Exists(iconPath))
            {
                shortcut.IconLocation = iconPath + ",0";
            }
            shortcut.Description = "Aegis AI - The Autonomous Desktop AI Companion";
            shortcut.Save();
        }

        private static void RegisterWindowsUninstall(string appDir)
        {
            try
            {
                string keyPath = @"Software\Microsoft\Windows\CurrentVersion\Uninstall\AegisAI";
                using (RegistryKey key = Registry.CurrentUser.CreateSubKey(keyPath))
                {
                    if (key != null)
                    {
                        key.SetValue("DisplayName", "Aegis AI (Desktop Companion)");
                        key.SetValue("DisplayVersion", "0.2.0-alpha");
                        key.SetValue("Publisher", "Mokashreef & Contributors");
                        key.SetValue("InstallLocation", appDir);
                        key.SetValue("DisplayIcon", Path.Combine(appDir, "assets", "icon.ico"));
                        key.SetValue("UninstallString", "\"" + Path.Combine(appDir, "AegisAI-Setup.exe") + "\" /uninstall");
                        key.SetValue("NoModify", 1, RegistryValueKind.DWord);
                        key.SetValue("NoRepair", 1, RegistryValueKind.DWord);
                    }
                }
            }
            catch { }
        }

        private static void LaunchApplication(string appDir)
        {
            try
            {
                string exePath = Path.Combine(appDir, "AegisAI.exe");
                if (File.Exists(exePath))
                {
                    ProcessStartInfo psi = new ProcessStartInfo(exePath);
                    psi.WorkingDirectory = appDir;
                    Process.Start(psi);
                }
            }
            catch { }
        }

        private static int PerformSilentInstall(string targetDir)
        {
            try
            {
                TerminateExistingProcesses();
                Directory.CreateDirectory(targetDir);
                ExtractEmbeddedPackage(targetDir, null);
                CreateDesktopShortcut(targetDir);
                CreateStartMenuShortcut(targetDir);
                RegisterWindowsUninstall(targetDir);
                LaunchApplication(targetDir);
                return 0;
            }
            catch
            {
                return 1;
            }
        }

        private static int PerformUninstall(string appDir, bool silent)
        {
            try
            {
                if (!silent)
                {
                    DialogResult res = MessageBox.Show(
                        "هل أنت متأكد من رغبتك في إلغاء تثبيت Aegis AI؟\nAre you sure you want to uninstall Aegis AI?",
                        "Aegis AI Uninstall",
                        MessageBoxButtons.YesNo,
                        MessageBoxIcon.Question
                    );
                    if (res != DialogResult.Yes) return 0;
                }

                TerminateExistingProcesses();

                // Remove shortcuts
                string desktopLnk = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), "Aegis AI.lnk");
                if (File.Exists(desktopLnk)) File.Delete(desktopLnk);

                string startMenuLnk = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), "Aegis AI.lnk");
                if (File.Exists(startMenuLnk)) File.Delete(startMenuLnk);

                // Remove uninstall registry key
                try
                {
                    Registry.CurrentUser.DeleteSubKeyTree(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\AegisAI", false);
                }
                catch { }

                // Schedule directory cleanup via background powershell script
                string cleanupCmd = "Start-Sleep -Seconds 2; Remove-Item -Path '" + appDir + "' -Recurse -Force -ErrorAction SilentlyContinue";
                ProcessStartInfo psi = new ProcessStartInfo("powershell.exe", "-NoProfile -Command \"" + cleanupCmd + "\"");
                psi.CreateNoWindow = true;
                psi.UseShellExecute = false;
                Process.Start(psi);

                if (!silent)
                {
                    MessageBox.Show("تم إلغاء تثبيت Aegis AI بنجاح.", "Aegis AI", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                return 0;
            }
            catch
            {
                return 1;
            }
        }
    }
}
