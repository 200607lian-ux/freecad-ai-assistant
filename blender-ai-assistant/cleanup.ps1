# Delete root directory temporary files
Remove-Item "6.3.md" -ErrorAction SilentlyContinue
Remove-Item "AUTO_3D_PREVIEW.md" -ErrorAction SilentlyContinue
Remove-Item "CHANGELOG_EXPORT.md" -ErrorAction SilentlyContinue
Remove-Item "CONNECTION_TROUBLESHOOTING.md" -ErrorAction SilentlyContinue
Remove-Item "COORDINATE_FIX_SUMMARY.md" -ErrorAction SilentlyContinue
Remove-Item "demo_export.py" -ErrorAction SilentlyContinue
Remove-Item "DOWNLOAD_FIX_GUIDE.md" -ErrorAction SilentlyContinue
Remove-Item "EXPORT_FEATURE_SUMMARY.md" -ErrorAction SilentlyContinue
Remove-Item "EXPORT_FORMATS_GUIDE.md" -ErrorAction SilentlyContinue
Remove-Item "FUTURE_DEVELOPMENT.md" -ErrorAction SilentlyContinue
Remove-Item "MULTI_FORMAT_EXPORT_README.md" -ErrorAction SilentlyContinue
Remove-Item "ORBITCONTROLS_FIX.md" -ErrorAction SilentlyContinue
Remove-Item "QUICK_START_EXPORT.md" -ErrorAction SilentlyContinue
Remove-Item "QUICK_START_GUIDE.md" -ErrorAction SilentlyContinue
Remove-Item "RESTART_GUIDE.md" -ErrorAction SilentlyContinue
Remove-Item "TEST_EXPORT_FEATURE.md" -ErrorAction SilentlyContinue
Remove-Item "test_new_export_ui.html" -ErrorAction SilentlyContinue
Remove-Item "THREEJS_FIX_SUMMARY.md" -ErrorAction SilentlyContinue
Remove-Item "TROUBLESHOOTING_3D_VIEWER.md" -ErrorAction SilentlyContinue
Remove-Item "UI_IMPROVEMENT_EXPORT.md" -ErrorAction SilentlyContinue
Remove-Item "UI_REDESIGN_SUMMARY.md" -ErrorAction SilentlyContinue
Remove-Item "USAGE_GUIDE.md" -ErrorAction SilentlyContinue
Remove-Item "导出功能文档索引.md" -ErrorAction SilentlyContinue
Remove-Item "新导出界面使用说明.md" -ErrorAction SilentlyContinue
Remove-Item "新功能说明.md" -ErrorAction SilentlyContinue

# Delete backend test files
Remove-Item "backend/diagnose_connection.py" -ErrorAction SilentlyContinue
Remove-Item "backend/final_test.py" -ErrorAction SilentlyContinue
Remove-Item "backend/hello_qwen.py" -ErrorAction SilentlyContinue
Remove-Item "backend/test_*.py" -ErrorAction SilentlyContinue
Remove-Item "backend/test_output.stl" -ErrorAction SilentlyContinue
Remove-Item "backend/*test*.py" -ErrorAction SilentlyContinue
Remove-Item "backend/websocket_example.py" -ErrorAction SilentlyContinue
Remove-Item "backend/verify_web_module.py" -ErrorAction SilentlyContinue

# Delete backend temporary documentation
Remove-Item "backend/AI_INTEGRATION_README.md" -ErrorAction SilentlyContinue
Remove-Item "backend/MAIN_AI_UPDATE.md" -ErrorAction SilentlyContinue
Remove-Item "backend/MATERIAL_FIX_GUIDE.md" -ErrorAction SilentlyContinue
Remove-Item "backend/QUICK_START_AI.md" -ErrorAction SilentlyContinue
Remove-Item "backend/STL_EXPORT_GUIDE.md" -ErrorAction SilentlyContinue
Remove-Item "backend/TEST_README.md" -ErrorAction SilentlyContinue
Remove-Item "backend/UPDATE_SUMMARY.md" -ErrorAction SilentlyContinue
Remove-Item "backend/WEB_SERVER_TEST.md" -ErrorAction SilentlyContinue

# Delete deprecated directories
Remove-Item "unused_tests" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "references" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Cleanup completed!" -ForegroundColor Green