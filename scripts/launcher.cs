using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Threading;
using System.Windows.Forms;

namespace AegisAI
{
    static class Program
    {
        private const string MutexName = "Global\\AegisAI_Desktop_Mutex_2026";

        [STAThread]
        static void Main(string[] args)
        {
            string appDir = AppDomain.CurrentDomain.BaseDirectory;
            Directory.SetCurrentDirectory(appDir);

            // Handle CLI flags
            bool isBackground = false;
            bool isInstallStartup = false;
            bool isRemoveStartup = false;

            foreach (string arg in args)
            {
                if (arg.Equals("--background", StringComparison.OrdinalIgnoreCase))
                    isBackground = true;
                else if (arg.Equals("--install-startup", StringComparison.OrdinalIgnoreCase))
                    isInstallStartup = true;
                else if (arg.Equals("--remove-startup", StringComparison.OrdinalIgnoreCase))
                    isRemoveStartup = true;
            }

            // Handle startup registration directly in Windows registry
            if (isInstallStartup || isRemoveStartup)
            {
                try
                {
                    using (var key = Microsoft.Win32.Registry.CurrentUser.OpenSubKey(
                        @"Software\Microsoft\Windows\CurrentVersion\Run", true))
                    {
                        if (key != null)
                        {
                            if (isInstallStartup)
                            {
                                string exePath = Path.Combine(appDir, "AegisAI.exe");
                                key.SetValue("AegisAI", "\"" + exePath + "\" --background");
                                MessageBox.Show(
                                    "Aegis AI has been successfully registered to start with Windows in background mode.\n\nتم تفعيل بدء تشغيل Aegis AI تلقائياً مع ويندوز.",
                                    "Aegis AI - Windows Startup",
                                    MessageBoxButtons.OK,
                                    MessageBoxIcon.Information
                                );
                            }
                            else if (isRemoveStartup)
                            {
                                key.DeleteValue("AegisAI", false);
                                MessageBox.Show(
                                    "Aegis AI has been removed from Windows Startup.\n\nتم إيقاف بدء تشغيل Aegis AI مع ويندوز.",
                                    "Aegis AI - Windows Startup",
                                    MessageBoxButtons.OK,
                                    MessageBoxIcon.Information
                                );
                            }
                        }
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show("Startup configuration error: " + ex.Message, "Aegis AI", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
                return;
            }

            // Check if Aegis is already running
            bool createdNew;
            using (Mutex mutex = new Mutex(true, MutexName, out createdNew))
            {
                if (!createdNew)
                {
                    // Already running: summon overlay window via local REST bridge
                    try
                    {
                        var req = (HttpWebRequest)WebRequest.Create("http://127.0.0.1:8420/api/desktop/show");
                        req.Method = "POST";
                        req.Timeout = 1500;
                        req.ContentLength = 0;
                        using (var resp = req.GetResponse()) { }
                    }
                    catch
                    {
                        // Ignore connection errors if port not ready
                    }
                    return;
                }

                // Terminate any stale orphan pythonw instances running from this directory
                try
                {
                    int myPid = Process.GetCurrentProcess().Id;
                    foreach (var proc in Process.GetProcessesByName("pythonw"))
                    {
                        try
                        {
                            if (proc.Id != myPid)
                            {
                                string exePath = proc.MainModule != null ? proc.MainModule.FileName : "";
                                if (!string.IsNullOrEmpty(exePath) && exePath.IndexOf("Aegis AI", StringComparison.OrdinalIgnoreCase) >= 0)
                                {
                                    proc.Kill();
                                    proc.WaitForExit(1000);
                                }
                            }
                        }
                        catch { }
                    }
                }
                catch { }

                // Locate isolated Python runtime (pythonw.exe prevents CMD console window)
                string pythonw = Path.Combine(appDir, ".venv", "Scripts", "pythonw.exe");
                string aegisPy = Path.Combine(appDir, "aegis.py");

                if (!File.Exists(pythonw))
                {
                    // Fallback to python.exe
                    pythonw = Path.Combine(appDir, ".venv", "Scripts", "python.exe");
                }

                if (!File.Exists(pythonw) || !File.Exists(aegisPy))
                {
                    MessageBox.Show(
                        "Could not locate Aegis AI runtime.\nPlease ensure '.venv' and 'aegis.py' exist in:\n" + appDir,
                        "Aegis AI - Runtime Error",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                    return;
                }

                string arguments = "\"" + aegisPy + "\"";
                if (isBackground)
                {
                    arguments += " --background";
                }

                ProcessStartInfo psi = new ProcessStartInfo
                {
                    FileName = pythonw,
                    Arguments = arguments,
                    WorkingDirectory = appDir,
                    CreateNoWindow = true,
                    UseShellExecute = false,
                    WindowStyle = ProcessWindowStyle.Hidden
                };

                try
                {
                    using (Process proc = Process.Start(psi))
                    {
                        if (proc != null)
                        {
                            // Keep launcher mutex alive until child process exits
                            proc.WaitForExit();
                        }
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show("Failed to launch Aegis AI: " + ex.Message, "Aegis AI", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }
    }
}

