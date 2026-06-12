# 清理顽固开机自启项 - 请以管理员身份运行此脚本
# 右键此文件选择 "使用 PowerShell 运行"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  清理开机自启项 & 无用服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$errors = @()

# ========== 注册表启动项 ==========
Write-Host ">>> 注册表启动项" -ForegroundColor Cyan

# Adobe Creative Cloud (HKLM)
Write-Host "  Adobe Creative Cloud..." -ForegroundColor Yellow -NoNewline
try {
    Remove-ItemProperty "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Run" -Name "Adobe Creative Cloud" -Force -ErrorAction Stop
    Write-Host " ✅ 已移除" -ForegroundColor Green
} catch { Write-Host " ❌ $_" -ForegroundColor Red; $errors += "Adobe CC" }

# Java Update (HKLM)
Write-Host "  Java Update Scheduler..." -ForegroundColor Yellow -NoNewline
try {
    Remove-ItemProperty "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Run" -Name "SunJavaUpdateSched" -Force -ErrorAction Stop
    Write-Host " ✅ 已移除" -ForegroundColor Green
} catch { Write-Host " ❌ $_" -ForegroundColor Red; $errors += "Java Update" }

# Steam (HKCU)
Write-Host "  Steam..." -ForegroundColor Yellow -NoNewline
try {
    Remove-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "Steam" -Force -ErrorAction Stop
    Write-Host " ✅ 已移除" -ForegroundColor Green
} catch { Write-Host " 可能已移除" -ForegroundColor Gray }

# ========== 计划任务 ==========
Write-Host ""
Write-Host ">>> 计划任务" -ForegroundColor Cyan

Write-Host "  LaunchDouyinGuard (抖音)..." -ForegroundColor Yellow -NoNewline
try {
    $task = Get-ScheduledTask -TaskName "LaunchDouyinGuard" -ErrorAction Stop
    Disable-ScheduledTask -TaskName "LaunchDouyinGuard" -ErrorAction Stop
    Write-Host " ✅ 已禁用" -ForegroundColor Green
} catch {
    try { schtasks /change /tn "LaunchDouyinGuard" /disable 2>$null; Write-Host " ✅ 已禁用" -ForegroundColor Green }
    catch { Write-Host " ❌" -ForegroundColor Red; $errors += "LaunchDouyinGuard" }
}

# ========== 服务 ==========
Write-Host ""
Write-Host ">>> 服务禁用" -ForegroundColor Cyan

$services = @{
    "PCManager Service Store" = "微软电脑管家"
    "QiyiService"             = "爱奇艺"
    "QQLiveService"           = "腾讯视频"
    "QQMusicService"          = "QQ音乐"
    "IObitUnSvr"              = "IObit 卸载器"
    "Origin Web Helper Service" = "EA Origin"
    "GamingServices"          = "Xbox 游戏服务"
    "GamingServicesNet"       = "Xbox 游戏服务(网络)"
    "Apple Mobile Device Service" = "Apple Mobile Device"
    "vmms"                    = "Hyper-V 虚拟机"
    "douyin_performance_service" = "抖音性能服务"
    "AndrowsSvr"              = "腾讯应用宝"
    "Killer Analytics Service" = "Killer 网卡分析"
    "Killer Network Service"  = "Killer 网卡网络"
    "DouyinElevationService"  = "抖音提权服务"
    "DouyinElevationService1da7150166e2e3c" = "抖音提权服务2"
    "LGHUBUpdaterService"     = "罗技更新"
    "GoTrust ID Plugin"       = "GoTrust ID 插件"
    "GoTrustID Service"       = "GoTrust ID 服务"
}

foreach ($svcName in $services.Keys) {
    $desc = $services[$svcName]
    Write-Host "  $desc ($svcName)..." -ForegroundColor Yellow -NoNewline
    try {
        $svc = Get-Service -Name $svcName -ErrorAction Stop
        Stop-Service -Name $svcName -Force -ErrorAction SilentlyContinue
        Set-Service -Name $svcName -StartupType Disabled -ErrorAction Stop
        Write-Host " ✅ 已禁用" -ForegroundColor Green
    } catch {
        Write-Host " (未找到)" -ForegroundColor Gray
    }
}

# ========== 终止运行中的进程 ==========
Write-Host ""
Write-Host ">>> 终止进程" -ForegroundColor Cyan

$killProcs = @("MSPCManager", "MSPCManagerCore", "MSPCManagerService", "douyin", "AndrowsStore", "QiyiService", "QQLiveService", "QQMusicService")
foreach ($proc in $killProcs) {
    try {
        $p = Get-Process -Name $proc -ErrorAction Stop
        Stop-Process -Name $proc -Force -ErrorAction Stop
        Write-Host "  ✅ 已终止: $proc" -ForegroundColor Green
    } catch { }
}

# ========== 结果 ==========
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "           清理完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

if ($errors.Count -gt 0) {
    Write-Host "以下项目未能处理:" -ForegroundColor Red
    foreach ($e in $errors) { Write-Host "  - $e" -ForegroundColor Red }
}

Write-Host ""
Write-Host "建议重启电脑感受效果~" -ForegroundColor Cyan
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
