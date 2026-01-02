#!/usr/bin/env python3
"""
Test script for OpenCode Service
Tests the integration between Auto-Code and OpenCode AI in Docker
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from src.services.opencode_service import OpenCodeService


async def test_container_status():
    """Test 1: Check if container is running"""
    print("=" * 60)
    print("TEST 1: Container Status")
    print("=" * 60)
    
    service = OpenCodeService()
    status = await service.get_container_status()
    
    print(f"✅ Container running: {status['running']}")
    print(f"✅ Container exists: {status['exists']}")
    print(f"\nOutput:\n{status['output']}")
    
    if not status['running']:
        print("\n❌ Container is not running!")
        print("Start it with: cd opencode-service && ./manage-opencode.sh start")
        return False
    
    return True


async def test_container_environment():
    """Test 2: Check container environment"""
    print("\n" + "=" * 60)
    print("TEST 2: Container Environment")
    print("=" * 60)
    
    service = OpenCodeService()
    
    # Test basic commands
    test_cmd = """
    echo "User: $(whoami)"
    echo "Home: $HOME"
    echo "Workspace: $(pwd)"
    echo "OpenCode binary: $(ls -lh /home/ubuntu/.opencode/bin/opencode 2>/dev/null || echo 'NOT FOUND')"
    echo "Git version: $(git --version)"
    echo "Python version: $(python3 --version)"
    echo "Node version: $(node --version 2>/dev/null || echo 'Not installed')"
    """
    
    proc = await asyncio.create_subprocess_exec(
        "docker", "exec", service.container_name,
        "/bin/bash", "-c", test_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await proc.communicate()
    
    if proc.returncode == 0:
        print("✅ Container environment check:")
        print(stdout.decode())
    else:
        print(f"❌ Environment check failed: {stderr.decode()}")
        return False
    
    return True


async def test_github_access():
    """Test 3: Check GitHub authentication"""
    print("\n" + "=" * 60)
    print("TEST 3: GitHub Access")
    print("=" * 60)
    
    service = OpenCodeService()
    
    # Check if GH_TOKEN is available
    gh_test_cmd = """
    if [ -n "$GH_TOKEN" ]; then
        echo "✅ GH_TOKEN is set (length: ${#GH_TOKEN})"
        echo "Testing GitHub CLI..."
        gh --version
    else
        echo "❌ GH_TOKEN is not set"
        exit 1
    fi
    """
    
    proc = await asyncio.create_subprocess_exec(
        "docker", "exec", service.container_name,
        "/bin/bash", "-c", gh_test_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await proc.communicate()
    
    print(stdout.decode())
    
    if proc.returncode != 0:
        print(f"⚠️  Warning: {stderr.decode()}")
        return False
    
    return True


async def test_clone_repository():
    """Test 4: Clone a test repository"""
    print("\n" + "=" * 60)
    print("TEST 4: Clone Repository")
    print("=" * 60)
    
    service = OpenCodeService()
    
    # Use a small public repository for testing
    test_repo_url = "https://github.com/octocat/Hello-World.git"
    
    print(f"📦 Cloning test repository: {test_repo_url}")
    
    repo_path = await service.clone_or_update_repository(
        repo_url=test_repo_url,
        github_token=os.getenv("GH_TOKEN")
    )
    
    if repo_path:
        print(f"✅ Repository cloned successfully to: {repo_path}")
        
        # List files in the repository
        list_cmd = f"ls -la {repo_path}"
        proc = await asyncio.create_subprocess_exec(
            "docker", "exec", service.container_name,
            "/bin/bash", "-c", list_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        print(f"\nFiles in repository:\n{stdout.decode()}")
        return True
    else:
        print("❌ Failed to clone repository")
        return False


async def test_opencode_executable():
    """Test 5: Check if OpenCode is executable"""
    print("\n" + "=" * 60)
    print("TEST 5: OpenCode Executable")
    print("=" * 60)
    
    service = OpenCodeService()
    
    # Test OpenCode binary
    opencode_test_cmd = """
    OPENCODE_BIN=/home/ubuntu/.opencode/bin/opencode
    
    if [ -f "$OPENCODE_BIN" ]; then
        echo "✅ OpenCode binary exists"
        echo "File info: $(ls -lh $OPENCODE_BIN)"
        echo ""
        echo "Testing OpenCode version..."
        $OPENCODE_BIN --version 2>&1 || echo "Version command not available"
        echo ""
        echo "Testing OpenCode help..."
        $OPENCODE_BIN --help 2>&1 | head -20 || echo "Help command not available"
    else
        echo "❌ OpenCode binary not found at $OPENCODE_BIN"
        exit 1
    fi
    """
    
    proc = await asyncio.create_subprocess_exec(
        "docker", "exec", service.container_name,
        "/bin/bash", "-c", opencode_test_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await proc.communicate()
    
    print(stdout.decode())
    
    if proc.returncode != 0:
        print(f"❌ Error: {stderr.decode()}")
        return False
    
    return True


async def test_opencode_auth():
    """Test 6: Check OpenCode authentication"""
    print("\n" + "=" * 60)
    print("TEST 6: OpenCode Authentication")
    print("=" * 60)
    
    service = OpenCodeService()
    
    auth_test_cmd = """
    AUTH_FILE=/home/ubuntu/.local/share/opencode/auth.json
    
    if [ -f "$AUTH_FILE" ]; then
        echo "✅ OpenCode auth file exists"
        echo "File size: $(du -h $AUTH_FILE | cut -f1)"
        echo ""
        echo "Testing OpenCode auth status..."
        /home/ubuntu/.opencode/bin/opencode auth status 2>&1 || echo "Auth status not available"
    else
        echo "⚠️  OpenCode auth file not found at $AUTH_FILE"
        echo ""
        echo "To authenticate OpenCode:"
        echo "  1. On host: opencode auth login"
        echo "  2. Or in container: docker exec -it autocode-opencode /home/ubuntu/.opencode/bin/opencode auth login"
        exit 1
    fi
    """
    
    proc = await asyncio.create_subprocess_exec(
        "docker", "exec", service.container_name,
        "/bin/bash", "-c", auth_test_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await proc.communicate()
    
    print(stdout.decode())
    
    if proc.returncode != 0:
        print("⚠️  OpenCode is not authenticated yet")
        print("This is normal if you haven't run 'opencode auth login'")
        return False
    
    return True


async def test_simple_task():
    """Test 7: Run a simple OpenCode task (if authenticated)"""
    print("\n" + "=" * 60)
    print("TEST 7: Simple OpenCode Task (Optional)")
    print("=" * 60)
    
    service = OpenCodeService()
    
    # Create a test project
    create_project_cmd = """
    cd /home/ubuntu/workspace
    rm -rf test-opencode-project
    mkdir -p test-opencode-project
    cd test-opencode-project
    git init
    echo "# Test Project" > README.md
    git add README.md
    git commit -m "Initial commit" 2>/dev/null || echo "Git user not configured"
    echo "✅ Test project created at: $(pwd)"
    """
    
    proc = await asyncio.create_subprocess_exec(
        "docker", "exec", service.container_name,
        "/bin/bash", "-c", create_project_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await proc.communicate()
    print(stdout.decode())
    
    print("\n⚠️  To test OpenCode with this project:")
    print("   docker exec -it autocode-opencode /bin/bash")
    print("   cd /home/ubuntu/workspace/test-opencode-project")
    print("   echo 'Create a hello.py file with a hello world function' | /home/ubuntu/.opencode/bin/opencode .")
    
    return True


async def main():
    """Run all tests"""
    print("\n" + "🧪" * 30)
    print("  OPENCODE SERVICE TEST SUITE")
    print("🧪" * 30 + "\n")
    
    tests = [
        ("Container Status", test_container_status),
        ("Container Environment", test_container_environment),
        ("GitHub Access", test_github_access),
        ("Clone Repository", test_clone_repository),
        ("OpenCode Executable", test_opencode_executable),
        ("OpenCode Authentication", test_opencode_auth),
        ("Simple Task Setup", test_simple_task),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! OpenCode service is ready to use.")
    elif passed >= 5:
        print("\n⚠️  Most tests passed. Check OpenCode authentication.")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
