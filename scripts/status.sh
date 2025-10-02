#!/bin/bash
# Quick status check for all jobs

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Air-Executor Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

for job_dir in .air-executor/jobs/*/; do
  if [ -d "$job_dir" ]; then
    jobname=$(basename "$job_dir")
    state_file="${job_dir}state.json"
    tasks_file="${job_dir}tasks.json"
    
    if [ -f "$state_file" ]; then
      state=$(jq -r .state "$state_file" 2>/dev/null || echo "unknown")
      updated=$(jq -r .updated_at "$state_file" 2>/dev/null || echo "unknown")
      
      # Color-code states
      case $state in
        completed) color="\033[0;32m" ;;  # Green
        working)   color="\033[0;33m" ;;  # Yellow
        failed)    color="\033[0;31m" ;;  # Red
        waiting)   color="\033[0;36m" ;;  # Cyan
        *)         color="\033[0m" ;;     # Default
      esac
      
      echo -e "${color}📦 Job: $jobname\033[0m"
      echo -e "   State: ${color}$state\033[0m"
      echo "   Updated: $updated"
      
      if [ -f "$tasks_file" ]; then
        total=$(jq 'length' "$tasks_file" 2>/dev/null || echo 0)
        completed=$(jq '[.[] | select(.status=="completed")] | length' "$tasks_file" 2>/dev/null || echo 0)
        failed=$(jq '[.[] | select(.status=="failed")] | length' "$tasks_file" 2>/dev/null || echo 0)
        pending=$(jq '[.[] | select(.status=="pending")] | length' "$tasks_file" 2>/dev/null || echo 0)
        running=$(jq '[.[] | select(.status=="running")] | length' "$tasks_file" 2>/dev/null || echo 0)
        
        echo "   Tasks: $completed/$total completed"
        if [ $running -gt 0 ]; then
          echo "   🔄 Running: $running"
        fi
        if [ $pending -gt 0 ]; then
          echo "   ⏳ Pending: $pending"
        fi
        if [ $failed -gt 0 ]; then
          echo "   ❌ Failed: $failed"
        fi
      fi
      echo ""
    fi
  fi
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
