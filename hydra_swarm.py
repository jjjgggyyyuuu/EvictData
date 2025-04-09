#!/usr/bin/env python3
import os
import sys
import subprocess
import threading
import queue
import argparse
import time
import random
from typing import List, Dict, Any, Optional

class HydraAgent:
    def __init__(self, agent_id: int, target: str, service: str):
        self.agent_id = agent_id
        self.target = target
        self.service = service
        self.running = False
        self.results = []
        self.process = None
    
    def start_attack(self, username_list: str, password_list: str, 
                     start_line: int = 0, end_line: int = None, 
                     tasks: int = 16) -> None:
        """Start a Hydra password cracking attack"""
        self.running = True
        
        # Split password list if needed
        if end_line:
            temp_pw_list = f"temp_pw_list_{self.agent_id}.txt"
            with open(password_list, 'r') as source:
                with open(temp_pw_list, 'w') as target:
                    for i, line in enumerate(source):
                        if i >= start_line and (end_line is None or i < end_line):
                            target.write(line)
            password_list = temp_pw_list
        
        cmd = [
            "hydra",
            "-L", username_list,
            "-P", password_list,
            "-t", str(tasks),
            "-o", f"results_{self.agent_id}.txt",
            "-V",
            self.target,
            self.service
        ]
        
        print(f"[Agent {self.agent_id}] Starting attack with command: {' '.join(cmd)}")
        
        self.process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Monitor the output
        for line in self.process.stdout:
            if "password:" in line.lower():
                self.results.append(line.strip())
                print(f"[Agent {self.agent_id}] Found credential: {line.strip()}")
        
        self.running = False
        
        # Clean up temp file if created
        if end_line and os.path.exists(f"temp_pw_list_{self.agent_id}.txt"):
            os.remove(f"temp_pw_list_{self.agent_id}.txt")
    
    def stop_attack(self) -> None:
        """Stop the current attack"""
        if self.process and self.running:
            self.process.terminate()
            self.running = False
            print(f"[Agent {self.agent_id}] Attack stopped")
    
    def get_results(self) -> List[str]:
        """Get current results"""
        return self.results

class SwarmController:
    def __init__(self, target: str, service: str, username_list: str, 
                 password_list: str, num_agents: int = 4):
        self.target = target
        self.service = service
        self.username_list = username_list
        self.password_list = password_list
        self.num_agents = num_agents
        self.agents = []
        self.threads = []
        self.results = []
        
    def prepare_workload(self) -> List[Dict[str, Any]]:
        """Split the password list into chunks for each agent"""
        # Count total passwords
        with open(self.password_list, 'r') as f:
            total_passwords = sum(1 for _ in f)
        
        chunk_size = total_passwords // self.num_agents
        workloads = []
        
        for i in range(self.num_agents):
            start = i * chunk_size
            # Last agent takes any remainder
            end = None if i == self.num_agents - 1 else (i + 1) * chunk_size
            
            workloads.append({
                "agent_id": i,
                "start_line": start,
                "end_line": end
            })
        
        return workloads
    
    def start_swarm(self) -> None:
        """Initialize and start all agents in the swarm"""
        workloads = self.prepare_workload()
        
        for workload in workloads:
            agent = HydraAgent(workload["agent_id"], self.target, self.service)
            self.agents.append(agent)
            
            thread = threading.Thread(
                target=agent.start_attack,
                args=(
                    self.username_list,
                    self.password_list,
                    workload["start_line"],
                    workload["end_line"]
                )
            )
            
            self.threads.append(thread)
            thread.start()
            
            # Small delay to prevent overwhelming the target
            time.sleep(1)
            
        print(f"[Swarm] All {self.num_agents} agents deployed")
    
    def monitor_swarm(self) -> None:
        """Monitor the swarm status and collect results"""
        try:
            while any(agent.running for agent in self.agents):
                time.sleep(5)
                active_agents = sum(1 for agent in self.agents if agent.running)
                print(f"[Swarm] Status: {active_agents}/{self.num_agents} agents still running")
                
                # Collect any new results
                for agent in self.agents:
                    new_results = [r for r in agent.get_results() if r not in self.results]
                    self.results.extend(new_results)
                
        except KeyboardInterrupt:
            print("[Swarm] Stopping all agents...")
            for agent in self.agents:
                agent.stop_attack()
    
    def wait_for_completion(self) -> None:
        """Wait for all agent threads to complete"""
        for thread in self.threads:
            thread.join()
    
    def get_all_results(self) -> List[str]:
        """Combine and return all results from agents"""
        all_results = []
        
        # Collect from memory
        for agent in self.agents:
            all_results.extend(agent.get_results())
        
        # Also collect from result files (in case some weren't captured in memory)
        for i in range(self.num_agents):
            result_file = f"results_{i}.txt"
            if os.path.exists(result_file):
                with open(result_file, 'r') as f:
                    all_results.extend([line.strip() for line in f if line.strip()])
        
        # Remove duplicates
        return list(set(all_results))

def main():
    parser = argparse.ArgumentParser(description="Hydra Swarm - Distributed password cracking")
    parser.add_argument("-t", "--target", required=True, help="Target host (IP or hostname)")
    parser.add_argument("-s", "--service", required=True, help="Service to attack (ssh, ftp, etc.)")
    parser.add_argument("-L", "--userlist", required=True, help="Path to username list file")
    parser.add_argument("-P", "--passlist", required=True, help="Path to password list file")
    parser.add_argument("-a", "--agents", type=int, default=4, help="Number of agents in swarm")
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("Hydra Swarm - Distributed Password Cracking Tool")
    print("=" * 50)
    print(f"Target: {args.target}")
    print(f"Service: {args.service}")
    print(f"Username list: {args.userlist}")
    print(f"Password list: {args.passlist}")
    print(f"Number of agents: {args.agents}")
    print("-" * 50)
    
    if not os.path.exists(args.userlist):
        print(f"Error: Username list file not found: {args.userlist}")
        sys.exit(1)
    
    if not os.path.exists(args.passlist):
        print(f"Error: Password list file not found: {args.passlist}")
        sys.exit(1)
    
    # Check if Hydra is installed
    try:
        subprocess.run(["hydra", "-h"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("Error: Hydra is not installed or not in PATH. Please install Hydra first.")
        print("On Kali Linux: sudo apt-get install hydra")
        sys.exit(1)
    
    # Start the swarm
    swarm = SwarmController(
        args.target,
        args.service,
        args.userlist,
        args.passlist,
        args.agents
    )
    
    start_time = time.time()
    swarm.start_swarm()
    
    try:
        swarm.monitor_swarm()
        swarm.wait_for_completion()
    except KeyboardInterrupt:
        print("\n[!] Attack interrupted by user")
    
    # Print results
    results = swarm.get_all_results()
    
    print("\n" + "=" * 50)
    print("ATTACK RESULTS")
    print("=" * 50)
    
    if results:
        print(f"Found {len(results)} valid credentials:")
        for result in results:
            print(f"[+] {result}")
    else:
        print("No valid credentials found.")
    
    elapsed_time = time.time() - start_time
    print(f"\nTotal attack time: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main() 